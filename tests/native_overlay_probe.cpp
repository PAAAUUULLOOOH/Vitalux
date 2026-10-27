// Small real OpenGL/Vulkan present loops for the bundled overlay, both ELF ABIs.
#define VK_USE_PLATFORM_XLIB_KHR
#include <X11/Xlib.h>
#include <GL/glx.h>
#include <vulkan/vulkan.h>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <thread>
#include <vector>

static void check(VkResult value,const char* operation) {
    if(value!=VK_SUCCESS && value!=VK_SUBOPTIMAL_KHR) {
        std::fprintf(stderr,"%s failed: %d\n",operation,int(value));std::exit(2);
    }
}
static double now() {
    return std::chrono::duration<double>(std::chrono::steady_clock::now().time_since_epoch()).count();
}

int main(int argc,char** argv) {
    if(argc!=3)return 2;
    const bool use_vk=std::strcmp(argv[1],"vk")==0;
    const double seconds=std::atof(argv[2]);
    Display* display=XOpenDisplay(nullptr);
    if(!display){std::fputs("No actual X display\n",stderr);return 2;}
    const int screen=DefaultScreen(display);
    XVisualInfo* visual=nullptr;
    GLXContext context=nullptr;
    Window window;
    if(use_vk) {
        window=XCreateSimpleWindow(display,RootWindow(display,screen),0,0,640,480,0,0,0);
    } else {
        int attributes[]={GLX_RGBA,GLX_DOUBLEBUFFER,GLX_DEPTH_SIZE,16,None};
        visual=glXChooseVisual(display,screen,attributes);
        if(!visual)return 2;
        XSetWindowAttributes attributes_x{};
        attributes_x.colormap=XCreateColormap(display,RootWindow(display,screen),visual->visual,AllocNone);
        attributes_x.event_mask=StructureNotifyMask;
        window=XCreateWindow(display,RootWindow(display,screen),0,0,640,480,0,visual->depth,
                             InputOutput,visual->visual,CWColormap|CWEventMask,&attributes_x);
        context=glXCreateContext(display,visual,nullptr,True);
        if(!context)return 2;
    }
    char title[100];std::snprintf(title,sizeof(title),"Vitalux %s %zu-bit overlay probe",use_vk?"Vulkan":"OpenGL",sizeof(void*)*8);
    XStoreName(display,window,title);XMapWindow(display,window);XSync(display,False);
    unsigned frames=0;
    if(!use_vk) {
        if(!glXMakeCurrent(display,window,context))return 2;
        const double started=now();
        while(now()-started<seconds) {
            glClearColor(.05f,.08f+float(std::sin(frames*.02))*.02f,.16f,1.f);
            glClear(GL_COLOR_BUFFER_BIT);glXSwapBuffers(display,window);++frames;
            std::this_thread::sleep_for(std::chrono::milliseconds(8));
        }
        glFinish();glXMakeCurrent(display,None,nullptr);glXDestroyContext(display,context);XFree(visual);
    } else {
        VkApplicationInfo application{VK_STRUCTURE_TYPE_APPLICATION_INFO};
        application.pApplicationName="Vitalux native overlay verification";application.apiVersion=VK_API_VERSION_1_0;
        const char* extensions[]={VK_KHR_SURFACE_EXTENSION_NAME,VK_KHR_XLIB_SURFACE_EXTENSION_NAME};
        VkInstanceCreateInfo create{VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO};
        create.pApplicationInfo=&application;create.enabledExtensionCount=2;create.ppEnabledExtensionNames=extensions;
        VkInstance instance;check(vkCreateInstance(&create,nullptr,&instance),"vkCreateInstance");
        VkXlibSurfaceCreateInfoKHR surface_create{VK_STRUCTURE_TYPE_XLIB_SURFACE_CREATE_INFO_KHR};
        surface_create.dpy=display;surface_create.window=window;
        VkSurfaceKHR surface;check(vkCreateXlibSurfaceKHR(instance,&surface_create,nullptr,&surface),"vkCreateXlibSurface");
        uint32_t count=0;check(vkEnumeratePhysicalDevices(instance,&count,nullptr),"physical devices");
        if(!count)return 2;
        std::vector<VkPhysicalDevice> devices(count);check(vkEnumeratePhysicalDevices(instance,&count,devices.data()),"physical devices");
        VkPhysicalDevice physical=VK_NULL_HANDLE;uint32_t family=0;
        for(auto candidate:devices) {
            uint32_t n=0;vkGetPhysicalDeviceQueueFamilyProperties(candidate,&n,nullptr);
            std::vector<VkQueueFamilyProperties> families(n);vkGetPhysicalDeviceQueueFamilyProperties(candidate,&n,families.data());
            for(uint32_t i=0;i<n;++i) {
                VkBool32 present=VK_FALSE;check(vkGetPhysicalDeviceSurfaceSupportKHR(candidate,i,surface,&present),"surface support");
                if(present && (families[i].queueFlags&VK_QUEUE_GRAPHICS_BIT)){physical=candidate;family=i;break;}
            }
            if(physical)break;
        }
        if(!physical)return 2;
        float priority=1.f;
        VkDeviceQueueCreateInfo queue_create{VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO};
        queue_create.queueFamilyIndex=family;queue_create.queueCount=1;queue_create.pQueuePriorities=&priority;
        const char* device_extensions[]={VK_KHR_SWAPCHAIN_EXTENSION_NAME};
        VkDeviceCreateInfo device_create{VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO};
        device_create.queueCreateInfoCount=1;device_create.pQueueCreateInfos=&queue_create;
        device_create.enabledExtensionCount=1;device_create.ppEnabledExtensionNames=device_extensions;
        VkDevice device;check(vkCreateDevice(physical,&device_create,nullptr,&device),"vkCreateDevice");
        VkQueue queue;vkGetDeviceQueue(device,family,0,&queue);
        VkSurfaceCapabilitiesKHR caps;check(vkGetPhysicalDeviceSurfaceCapabilitiesKHR(physical,surface,&caps),"surface capabilities");
        count=0;check(vkGetPhysicalDeviceSurfaceFormatsKHR(physical,surface,&count,nullptr),"surface formats");
        std::vector<VkSurfaceFormatKHR> formats(count);check(vkGetPhysicalDeviceSurfaceFormatsKHR(physical,surface,&count,formats.data()),"surface formats");
        if(formats.empty())return 2;
        auto format=formats.front();if(format.format==VK_FORMAT_UNDEFINED)format.format=VK_FORMAT_B8G8R8A8_UNORM;
        VkSwapchainCreateInfoKHR swap_create{VK_STRUCTURE_TYPE_SWAPCHAIN_CREATE_INFO_KHR};
        swap_create.surface=surface;swap_create.minImageCount=caps.minImageCount+1;
        if(caps.maxImageCount && swap_create.minImageCount>caps.maxImageCount)swap_create.minImageCount=caps.maxImageCount;
        swap_create.imageFormat=format.format;swap_create.imageColorSpace=format.colorSpace;
        swap_create.imageExtent=caps.currentExtent.width==UINT32_MAX?VkExtent2D{640,480}:caps.currentExtent;
        swap_create.imageArrayLayers=1;swap_create.imageUsage=VK_IMAGE_USAGE_TRANSFER_DST_BIT|VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT;
        swap_create.imageSharingMode=VK_SHARING_MODE_EXCLUSIVE;swap_create.preTransform=caps.currentTransform;
        swap_create.compositeAlpha=VkCompositeAlphaFlagBitsKHR(caps.supportedCompositeAlpha&-caps.supportedCompositeAlpha);
        swap_create.presentMode=VK_PRESENT_MODE_FIFO_KHR;swap_create.clipped=VK_TRUE;
        VkSwapchainKHR swapchain;check(vkCreateSwapchainKHR(device,&swap_create,nullptr,&swapchain),"vkCreateSwapchain");
        count=0;check(vkGetSwapchainImagesKHR(device,swapchain,&count,nullptr),"swapchain images");
        std::vector<VkImage> images(count);check(vkGetSwapchainImagesKHR(device,swapchain,&count,images.data()),"swapchain images");
        VkCommandPoolCreateInfo pool_create{VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO};
        pool_create.queueFamilyIndex=family;pool_create.flags=VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;
        VkCommandPool pool;check(vkCreateCommandPool(device,&pool_create,nullptr,&pool),"command pool");
        VkCommandBufferAllocateInfo allocate{VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO};
        allocate.commandPool=pool;allocate.level=VK_COMMAND_BUFFER_LEVEL_PRIMARY;allocate.commandBufferCount=1;
        VkCommandBuffer commands;check(vkAllocateCommandBuffers(device,&allocate,&commands),"command buffer");
        VkSemaphoreCreateInfo sem_create{VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO};
        VkSemaphore ready,drawn;check(vkCreateSemaphore(device,&sem_create,nullptr,&ready),"acquire semaphore");
        check(vkCreateSemaphore(device,&sem_create,nullptr,&drawn),"present semaphore");
        const double started=now();
        while(now()-started<seconds) {
            uint32_t image_index;
            check(vkAcquireNextImageKHR(device,swapchain,UINT64_MAX,ready,VK_NULL_HANDLE,&image_index),"acquire image");
            check(vkResetCommandBuffer(commands,0),"reset commands");
            VkCommandBufferBeginInfo begin{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
            check(vkBeginCommandBuffer(commands,&begin),"begin commands");
            VkImageMemoryBarrier barrier{VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER};
            barrier.oldLayout=VK_IMAGE_LAYOUT_UNDEFINED;barrier.newLayout=VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
            barrier.srcQueueFamilyIndex=barrier.dstQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED;
            barrier.image=images[image_index];barrier.subresourceRange={VK_IMAGE_ASPECT_COLOR_BIT,0,1,0,1};
            barrier.dstAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT;
            vkCmdPipelineBarrier(commands,VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,0,0,nullptr,0,nullptr,1,&barrier);
            VkClearColorValue color{{.05f,.08f+float(std::sin(frames*.02))*.02f,.16f,1.f}};
            vkCmdClearColorImage(commands,images[image_index],VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,&color,1,&barrier.subresourceRange);
            barrier.oldLayout=VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;barrier.newLayout=VK_IMAGE_LAYOUT_PRESENT_SRC_KHR;
            barrier.srcAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT;barrier.dstAccessMask=0;
            vkCmdPipelineBarrier(commands,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT,0,0,nullptr,0,nullptr,1,&barrier);
            check(vkEndCommandBuffer(commands),"end commands");
            VkPipelineStageFlags wait_stage=VK_PIPELINE_STAGE_TRANSFER_BIT;
            VkSubmitInfo submit{VK_STRUCTURE_TYPE_SUBMIT_INFO};
            submit.waitSemaphoreCount=1;submit.pWaitSemaphores=&ready;submit.pWaitDstStageMask=&wait_stage;
            submit.commandBufferCount=1;submit.pCommandBuffers=&commands;submit.signalSemaphoreCount=1;submit.pSignalSemaphores=&drawn;
            check(vkQueueSubmit(queue,1,&submit,VK_NULL_HANDLE),"queue submit");
            VkPresentInfoKHR present{VK_STRUCTURE_TYPE_PRESENT_INFO_KHR};
            present.waitSemaphoreCount=1;present.pWaitSemaphores=&drawn;present.swapchainCount=1;
            present.pSwapchains=&swapchain;present.pImageIndices=&image_index;
            check(vkQueuePresentKHR(queue,&present),"queue present");check(vkQueueWaitIdle(queue),"queue idle");++frames;
        }
        check(vkDeviceWaitIdle(device),"device idle");
        vkDestroySemaphore(device,ready,nullptr);vkDestroySemaphore(device,drawn,nullptr);
        vkDestroyCommandPool(device,pool,nullptr);vkDestroySwapchainKHR(device,swapchain,nullptr);
        vkDestroyDevice(device,nullptr);vkDestroySurfaceKHR(instance,surface,nullptr);vkDestroyInstance(instance,nullptr);
    }
    XDestroyWindow(display,window);XCloseDisplay(display);
    std::printf("api=%s bits=%zu frames=%u\n",use_vk?"vk":"gl",sizeof(void*)*8,frames);
    return frames?0:2;
}
