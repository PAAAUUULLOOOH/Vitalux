"""Independent channel browsing, verified packages and graceful automatic restarts."""
import hashlib
import json
import math
import os
import time
from pathlib import Path

from PySide6.QtCore import QObject, QThread, QTimer, Signal

from . import __version__, updater, profiles, versions, changelog, logfiles, events
from .i18n import tr
from .update_state import UpdatePhase


class _CheckThread(QThread):
    done = Signal(object)

    def run(self):
        try:self.done.emit(updater.catalog())
        except Exception as exc:self.done.emit({'error':str(exc)})


def _stable_target(records, candidate):
    """Resolve only fresh, verified parity covering both running and staged code."""
    stable=records.get('stable',{});test=records.get('unstable',{})
    if not all(record.get('ok') and not record.get('stale') for record in (stable,test)):return None
    if not (test.get('manifest_verified') is True and test.get('stable_verified') is True and
            test.get('has_test_changes') is False and not test.get('eligible') and
            (test.get('same_as_stable') is True or test.get('stable_contains_test') is True)):return None
    try:
        covered=test.get('covered_test_version') or test['latest']
        if versions.channel(covered)!='unstable':return None
        if (stable['latest']!=test['stable_version'] or versions.channel(stable['latest'])!='stable' or
                not (versions.channel(test['latest'])=='unstable' or test['latest']==stable['latest']) or
                versions.parse(stable['latest'])[0]<versions.parse(__version__)[0] or
                versions.key(stable['latest'])<versions.key(candidate) or
                versions.key(covered)<versions.key(candidate) or
                (versions.channel(__version__)=='unstable' and versions.key(covered)<versions.key(__version__))):return None
        if not stable.get('url') or len(stable.get('sha256',''))!=64:return None
        int(stable['sha256'],16)
        return stable
    except (KeyError,ValueError,TypeError):return None


class _InstallThread(QThread):
    progress = Signal(float)
    phase_changed = Signal(object)
    done = Signal(str)

    def __init__(self, url, sha256, parent, pending=None):
        super().__init__(parent)
        self.url,self.sha256=url,sha256
        self.channel,self.version=parent.channel,parent.latest
        self.expected_size=parent.records.get(parent.channel,{}).get('bytes')
        self.pending_path=None
        self.kind='appimage' if updater.appimage_path() else 'zip'
        self.promotion_guard=self.channel=='unstable' and parent.records.get('unstable',{}).get('manifest_verified') is True
        if pending:
            self.channel,self.version=pending['channel'],pending['version']
            self.sha256=pending['sha256'];self.pending_path=pending.get('path');self.kind=pending['kind']
            self.promotion_guard=pending.get('promotion_guard',False)
        self.resume=bool(pending)
        self.transfer_progress = 100. if self.resume else 0.
        self.overall_progress = 98. if self.resume else 0.
        self.second_transfer = self.resume
        self.phase = None

    def _promoted_target(self):
        if self.channel!='unstable' or not self.promotion_guard:return None
        self._set_phase(UpdatePhase.PARITY)
        try:return _stable_target(updater.catalog(),self.version)
        except Exception:return None  # An offline check cannot authorize a channel change.

    def _use_stable(self,record):
        self.channel='stable';self.version=record['latest']
        self.url,self.sha256=record['url'],record['sha256'];self.expected_size=record.get('bytes')

    def _download(self):
        self.transfer_progress = 0.
        return updater.install(self.url,sha256=self.sha256,progress=self._report_progress,defer=True,expected_size=self.expected_size)

    def _set_phase(self, phase):
        if phase == self.phase:return
        self.phase = phase
        self.phase_changed.emit(phase)

    def _discard(self,path):
        # Only remove the exact, superseded staged file, never its profile directory.
        if path and path!=self.pending_path:
            try:
                candidate=Path(path);candidate.unlink(missing_ok=True)
                if self.kind=='zip' and candidate.parent.name.startswith('prepared-zip-'):
                    candidate.parent.rmdir()
            except OSError:pass

    def run(self):
        try:
            promoted=self._promoted_target()
            if promoted:self._use_stable(promoted)
            if self.channel!=profiles.installed():
                profiles.backup('stable');profiles.backup('unstable')
            if not self.resume or promoted:
                previous=self.pending_path
                self.pending_path=self._download()
                self._discard(previous)
            # Promotion can happen while the normal Unstable transfer is in flight.
            promoted=self._promoted_target()
            if promoted:
                previous=self.pending_path;self._use_stable(promoted)
                self.second_transfer = True
                profiles.backup('stable');profiles.backup('unstable')
                self.pending_path=self._download()
                self._discard(previous)
            profiles.select(self.channel)
            self.done.emit('')
        except Exception as exc:
            if not self.resume:
                abandoned,self.pending_path=self.pending_path,None
                self._discard(abandoned)
            reason=tr('Die Verbindung hat zu lange nicht geantwortet. Bitte den Download erneut versuchen.') if isinstance(exc,TimeoutError) else str(exc)
            self.done.emit(f"{tr('Installation fehlgeschlagen:')} {reason}")

    def _report_progress(self,value):
        self.transfer_progress = value
        if value<=80 and self.isInterruptionRequested():
            raise RuntimeError(tr('Download abgebrochen.'))
        self._set_phase((UpdatePhase.STABLE if self.channel=='stable' else UpdatePhase.DOWNLOAD) if value<80
                        else UpdatePhase.VERIFY if value<85 else UpdatePhase.PREPARE)
        mapped = 85. + value * .13 if self.second_transfer else value * .85
        self.overall_progress = max(self.overall_progress, min(99., mapped))
        self.progress.emit(self.overall_progress)


class _RestoreThread(QThread):
    done = Signal(str)
    pending_path=None

    def run(self):
        try:
            metadata=profiles.read(Path(updater.app_root())/'.backup/metadata.json')
            self.version=metadata.get('version','')
            self.channel=versions.channel(self.version)
            updater.restore_previous()
            self.done.emit('')
        except Exception as exc:self.done.emit(str(exc))


class UpdateManager(QObject):
    changed = Signal()
    progress = Signal(float)
    restart = Signal()

    def __init__(self):
        super().__init__()
        self.status='preview' if os.environ.get('VITALUX_LOCAL_PREVIEW')=='1' else 'idle'
        self.channel=profiles.installed()  # Tabs browse; only installation changes the channel.
        self.latest=self.notes=self.url=self.error=self.sha256=''
        self.error_kind='check'
        self.records={};self.last_checked=0.;self.last_attempt=0.
        self.checking=False;self.progress_value=0.;self.cancelling=False
        self.phase = UpdatePhase.DOWNLOAD
        self.pending_path=None;self.pending_restart=False;self.pending={}
        self._activation_started=False;self._restart_requested=False
        self._pending_checked=False
        self.automatic_stable_return=False;self._auto_return_attempted=set()
        self._auto_stable_timer=QTimer(self);self._auto_stable_timer.setSingleShot(True)
        self._auto_stable_timer.timeout.connect(self._return_to_stable)
        self.restart_attempts=0;self._restart_retrying=False
        self._relaunch_on_exit=False
        self._shutting_down=False;self._thread=None;self._active_threads=[]
        self._cache_path=profiles.directory('cache')/'release-catalog.json'
        application=os.path.realpath(updater.appimage_path() or updater.app_root())
        identity=hashlib.sha256(os.fsencode(application)).hexdigest()[:24]
        self._pending_file=profiles.root('state')/'updates'/identity/'pending.json'
        if self.status!='preview':self._load_cache();self._load_pending()
        self._timer=QTimer(self);self._timer.setInterval(6*3600*1000)
        self._timer.timeout.connect(self.check)
        self._restart_timer=QTimer(self);self._restart_timer.setSingleShot(True)
        self._restart_timer.timeout.connect(self._restart)
        if self.status!='preview' and not self.pending_restart:self._timer.start()
        self._select_record()
        if self.pending_restart:
            # A previous transient preparation failure must not require a
            # second confirmation on the next launch. Retry the verified target.
            self._restart_retrying=bool(self.error)
            self._restart_timer.start(200)

    @property
    def restart_retrying(self):
        return self._restart_retrying and self._restart_timer.isActive()

    def _restart_event(self,event,error=''):
        try:
            record=dict(time=time.time(),source=__version__,target=self.pending.get('version',''),
                        event=event,attempt=self.restart_attempts,error=error)
            self._pending_file.parent.mkdir(parents=True,exist_ok=True)
            logfiles.append(self._pending_file.with_name('restart-events.jsonl'),
                            json.dumps(record,ensure_ascii=False)+'\n')
        except OSError:pass

    def _load_cache(self):
        cached=profiles.read(self._cache_path)
        stamp=cached.get('checked_at',0)
        self.last_checked=stamp if isinstance(stamp,(int,float)) and math.isfinite(stamp) and 0<=stamp<=time.time()+300 else 0
        for channel,record in cached.get('records',{}).items() if isinstance(cached.get('records'),dict) else ():
            if (channel in ('stable','unstable') and isinstance(record,dict)
                    and isinstance(record.get('latest',''),str) and isinstance(record.get('notes',''),str)
                    and changelog.visible_version(record.get('latest',''))):
                # Cached notes are display-only. A fresh verified check authorizes installs.
                self.records[channel]=dict(record,stale=True,url='',sha256='',newer=False)
                stamp=record.get('checked_at',self.last_checked)
                if not isinstance(stamp,(int,float)) or not math.isfinite(stamp) or not 0<=stamp<=time.time()+300:
                    self.records[channel]['checked_at']=self.last_checked

    def _load_pending(self):
        pending=profiles.read(self._pending_file)
        if not changelog.visible_version(pending.get('version','')):return
        if pending.get('version')==__version__:
            try:self._pending_file.unlink(missing_ok=True)
            except OSError:pass
        elif pending.get('source_version')==__version__ and pending.get('channel') in ('stable','unstable'):
            path=pending.get('path')
            if path:
                if not isinstance(path,str) or not Path(path).is_file():return
                try:
                    with open(path,'rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
                    if digest!=pending.get('sha256'):return
                except OSError:return
            self.pending=pending;self.pending_path=path;self.pending_restart=True
            self.status='installed'
            self.error=pending.get('activation_error','')
            self.error_kind='restart'

    @property
    def notification_version(self):
        record=self.records.get(profiles.installed(),{})
        return record.get('latest','') if record.get('ok') else self.latest

    @property
    def available(self):
        if self.pending_restart or self.status in ('installing','installed','preview'):return False
        record=self.records.get(profiles.installed())
        if record is not None:
            return bool(record.get('ok') and not record.get('stale') and record.get('newer') and record.get('eligible',True))
        return self.status=='available' and self.channel==profiles.installed()

    @property
    def can_install(self):
        return (not self.pending_restart and not self.checking and self.status in ('available','switch_available')
                and bool(self.url) and bool(self.sha256))

    @property
    def stable_has_test_changes(self):
        if profiles.installed()!='unstable':return False
        stable=self.records.get('stable',{});test=self.records.get('unstable',{})
        try:
            return (bool(stable.get('ok')) and not stable.get('stale') and test.get('ok') and not test.get('stale') and not test.get('eligible',False)
                    and versions.parse(stable['latest'])[0]>=versions.parse(__version__)[0])
        except (ValueError,KeyError):return False

    @property
    def can_return_automatically(self):
        if profiles.installed()!='unstable' or self._shutting_down or self.checking or self.pending_restart or self.status in ('installing','installed','preview'):return False
        return _stable_target(self.records,__version__) is not None

    def _return_to_stable(self):
        if not self.can_return_automatically:return
        target=(self.records['stable']['latest'],self.records['stable']['sha256'])
        if target in self._auto_return_attempted:return
        self._auto_return_attempted.add(target)
        self.automatic_stable_return=True
        self.set_channel('stable')
        self.install()

    def _select_record(self):
        record=self.records.get(self.channel,{})
        self.latest=record.get('latest','');self.notes=record.get('notes','')
        self.url=record.get('url','') if not record.get('stale') else ''
        self.sha256=record.get('sha256','') if not record.get('stale') else ''
        if self.pending_restart:self.status='installed';return
        if self.status=='preview':return
        if self.checking:self.status='checking';return
        if not record:
            self.status='error' if self.error else 'idle';return
        if not record.get('ok') or record.get('stale'):
            self.status='error' if self.error or record.get('error') else 'idle';return
        if self.channel=='unstable' and not record.get('eligible',False):self.status='unavailable'
        elif record.get('newer') and self.url:
            self.status='available' if self.channel==profiles.installed() else 'switch_available'
        else:self.status='uptodate'

    def set_channel(self,channel):
        if channel not in ('stable','unstable') or self.status=='installing':return
        self.channel=channel
        self._select_record();self.changed.emit()
        if not self.records and not self.checking and not self.pending_restart:self.check()

    def _start_worker(self,worker):
        self._thread=worker;self._active_threads.append(worker)
        worker.finished.connect(lambda w=worker:self._active_threads.remove(w) if w in self._active_threads else None)
        worker.start()

    def check(self):
        if self._shutting_down or os.environ.get('VITALUX_LOCAL_PREVIEW')=='1':return
        if self.checking or self.pending_restart or self.status in ('installing','installed'):return
        self.checking=True;self.last_attempt=time.time();self.error='';self.error_kind='check'
        self._select_record();self.changed.emit()
        worker=_CheckThread(self);worker.done.connect(self._on_checked);self._start_worker(worker)

    def _on_checked(self,result):
        self.checking=False
        if self.pending_restart or self.status=='installing':return
        failures=[];success=False
        for channel in ('stable','unstable'):
            record=result.get(channel)
            if not isinstance(record,dict):continue
            if not changelog.visible_version(record.get('latest','')):continue
            if record.get('ok'):
                self.records[channel]=dict(record,stale=False,checked_at=time.time());success=True
            else:
                prior=self.records.get(channel,{})
                self.records[channel]=dict(prior,ok=False,stale=True,url='',sha256='',newer=False,
                                           error=record.get('error',''))
                failures.append(record.get('error',''))
        self.error=result.get('error','') or next((failure for failure in failures if failure),'')
        if self.error:events.record('update_failed', stage='check')
        if success:
            self.last_checked=time.time()
            try:profiles.atomic_json(self._cache_path,{'checked_at':self.last_checked,'records':self.records})
            except OSError:pass  # The verified in-memory result remains usable.
        elif result.get('error'):
            for record in self.records.values():record.update(stale=True,url='',sha256='',newer=False)
        self._select_record();self.changed.emit()
        # Only a complete fresh check may start the verified return, never cache loading.
        if not self.error and all(isinstance(result.get(c),dict) and result[c].get('ok') for c in ('stable','unstable')) and self.can_return_automatically:
            self._auto_stable_timer.start(0)

    def install(self):
        if self._shutting_down or os.environ.get('VITALUX_LOCAL_PREVIEW')=='1':return
        # The ordinary update action resolves parity itself; it does not depend
        # on a separate return button or the automatic-check timer winning a race.
        candidate=self.latest if self.latest and versions.channel(self.latest)=='unstable' else __version__
        if self.channel=='unstable' and self.can_return_automatically and _stable_target(self.records,candidate):
            self.automatic_stable_return=True;self.set_channel('stable')
        if not self.can_install:return
        self.phase = UpdatePhase.DOWNLOAD
        self.status='installing';self.cancelling=False;self.progress_value=0.;self.progress.emit(0.);self.changed.emit()
        worker=_InstallThread(self.url,self.sha256,self)
        worker.progress.connect(self._on_progress)
        worker.phase_changed.connect(self._on_phase)
        worker.done.connect(lambda error,w=worker:self._on_installed(error,w))
        self._start_worker(worker)

    def _on_progress(self,value):
        self.progress_value=max(self.progress_value,min(100.,float(value)))
        self.progress.emit(self.progress_value)

    def _on_phase(self, phase):
        self.phase = phase
        self.changed.emit()

    @property
    def can_cancel(self):
        worker = self._thread
        return self.status == 'installing' and isinstance(worker, _InstallThread) and not worker.resume and worker.transfer_progress < 80

    def cancel_install(self):
        if not self.can_cancel:return
        if isinstance(self._thread,_InstallThread):
            self.cancelling=True;self._thread.requestInterruption();self.changed.emit()

    def retry_install(self):
        if self.error_kind!='install' or self.status!='error':return
        if any(w.isRunning() for w in self._active_threads):return
        self.error='';self._select_record();self.install()

    def _on_installed(self,error,worker=None):
        cancelled = self.cancelling
        self.cancelling=False
        if error:
            if getattr(worker,'resume',False):
                self.status='installed';self.error=error;self.error_kind='restart'
                self.restart_attempts+=1;self._restart_retrying=self.restart_attempts<3
                if self._restart_retrying:self._restart_timer.start(600*2**(self.restart_attempts-1))
                self.changed.emit();return
            self.status='error';self.error=error;self.error_kind='install'
            if not cancelled:events.record('update_failed', stage='install')
            self.changed.emit();return
        worker=worker or self._thread
        self.pending_path=getattr(worker,'pending_path',None)
        self.pending={'source_version':__version__,'version':getattr(worker,'version',self.latest),
                      'channel':getattr(worker,'channel',self.channel),'path':self.pending_path,
                      'kind':getattr(worker,'kind','appimage' if self.pending_path else 'zip'),
                      'sha256':getattr(worker,'sha256',self.sha256),
                      'promotion_guard':bool(getattr(worker,'promotion_guard',False))}
        self.channel=self.pending['channel']
        self.automatic_stable_return|=self.channel=='stable' and profiles.installed()=='unstable'
        self._pending_checked=bool(getattr(worker,'resume',False))
        self.pending_restart=True;self.status='installed';self.error='';self._timer.stop()
        self.restart_attempts=0;self._restart_retrying=False
        self._restart_event('installation_prepared')
        self._on_phase(UpdatePhase.READY)
        self._on_progress(98. if self.pending.get('promotion_guard') and self.pending['channel']=='unstable' and not self._pending_checked else 100.)
        try:profiles.atomic_json(self._pending_file,self.pending)
        except OSError:pass
        self.changed.emit()
        self._restart_timer.start(200)

    def rollback(self):
        if self.pending_restart or updater.appimage_path() or self.checking or self.status=='installing' or not updater.backup_available():return
        self.phase=UpdatePhase.PREPARE;self.progress_value=0.;self.progress.emit(0.)
        self.status='installing';self.changed.emit()
        worker=_RestoreThread(self)
        worker.done.connect(lambda error,w=worker:self._on_installed(error,w))
        self._start_worker(worker)

    def _restart(self):
        if self._shutting_down or self._restart_requested:return
        self._restart_timer.stop()
        if self.pending.get('promotion_guard') and self.pending.get('channel')=='unstable' and not self._pending_checked:
            if self.status=='installing':return
            self.status='installing';self.changed.emit()
            worker=_InstallThread('',self.pending['sha256'],self,pending=dict(self.pending))
            worker.progress.connect(self._on_progress)
            worker.phase_changed.connect(self._on_phase)
            worker.done.connect(lambda error,w=worker:self._on_installed(error,w))
            self._start_worker(worker)
            return
        self._restart_requested=True;self._relaunch_on_exit=True
        self.restart_attempts+=1;self._restart_retrying=False
        self.error=''
        self._restart_event('restart_requested')
        self.changed.emit()
        self.restart.emit()

    def retry_restart(self):
        if not self.pending_restart or self._restart_requested or self._shutting_down:return
        self.restart_attempts=0
        self._restart()

    def prepare_exit(self):
        """Activate only after the window has finished stopping all workers."""
        if self.pending.get('promotion_guard') and self.pending.get('channel')=='unstable' and not self._pending_checked:
            # A manual exit or failed promotion must retain the staged package
            # for revalidation, never activate the superseded test build.
            return True
        if self.pending_path and self.pending_restart and not self._activation_started:
            try:
                if self.pending.get('kind','appimage')=='zip':
                    updater.activate_zip_update(self.pending_path,self.pending.get('sha256',''),self._pending_file,relaunch=self._relaunch_on_exit)
                else:updater.activate_appimage_update(self.pending_path,relaunch=self._relaunch_on_exit)
                self._activation_started=True
                self._restart_retrying=False
                self._restart_event('activation_prepared')
                if self.pending.pop('activation_error', None) is not None:
                    try:profiles.atomic_json(self._pending_file,self.pending)
                    except OSError:pass
            except Exception as exc:
                self.error=str(exc);self.error_kind='restart'
                self._restart_requested=False;self._relaunch_on_exit=False
                self.pending['activation_error']=self.error
                self._restart_event('activation_preparation_failed',self.error)
                try:profiles.atomic_json(self._pending_file,self.pending)
                except OSError:pass
                if self.restart_attempts<3:
                    self._restart_retrying=True
                    self._restart_timer.start(600*2**max(0,self.restart_attempts-1))
                else:
                    self._restart_retrying=False
                    self._restart_event('automatic_retries_exhausted',self.error)
                    events.record('update_failed', stage='restart')
                self.changed.emit();return False
        return True

    def finalize_exit(self):
        """Retain recovery for manual exits and prevent a second activation."""
        self.prepare_exit()

    def shutdown(self):
        self._shutting_down=True
        self._auto_stable_timer.stop();self._timer.stop();self._restart_timer.stop()
        if isinstance(self._thread,_InstallThread) and self._thread.isRunning() and self._thread.transfer_progress<80:
            self._thread.requestInterruption()
        return not any(worker.isRunning() for worker in self._active_threads)

    def resume_after_shutdown(self):
        self._shutting_down=False
        if self.status!='preview' and not self.pending_restart:self._timer.start()
