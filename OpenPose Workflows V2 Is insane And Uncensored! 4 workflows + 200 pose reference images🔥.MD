00:00:00
The ultimate pose changing workflows are here. You can now transform any character in any style into any pose you want with perfect accuracy. No need for complicated control nets anymore. The new Quinn image edit plus model handles everything. You can even process multiple characters at once. Just one click, no re-uploading, and every character automatically takes the pose you choose and gets saved separately. Even better, it works the other way, too. You can give one character image and apply multiple poses to it in batch

00:00:36
mode. Again, all automatically generated and saved individually. All of this is done with these four powerful workflows and the 200 readytouse skeleton poses I'll be showing you in this video. Without further ado, let's go. In this video, we're going to go over the open post workflows with QN ImageEdit Plus. We have four workflows here. Workflow number one is actually the one I want to show you and tell you that it doesn't work. Strange, right? But I'll explain why. This workflow is the standard QN

00:01:11
image edit plus workflow. But unlike models such as Flux or Nano Banana, if you want to apply a specific pose to a character, it's not directly possible. This model simply can't change the pose that way. For example, here I have two input images, image one and image two. In my prompt, I write the woman in image one has the pose of the woman in image two. But no matter how many times we generate the output, you'll see it doesn't give us a good result. Here we can see that in fact the woman from the

00:01:42
first image is missing and the model just reuses the woman from the second image. It only swaps the clothes and the AI doesn't really understand what we want. So what do we do here? We move on to workflow number two. And in this one we extract the skeleton pose from the second image. Here you upload your first image. And here you upload the second one. And all you have to do is click run. Now we get the skeleton output and you can see that it works perfectly. The woman from the first image has now taken

00:02:16
the pose of the woman in the second image. So the solution was to take the skeleton output from the reference pose image and with the help of this node, we were able to do that. Now how can we still get results using the first workflow? There's actually a way for that too. I've prepared a file that contains 200 pre-made skeleton poses all ready to use. If you look inside this folder, you'll see 200 of these skeletons ready for you. You can simply drag and drop any of them into workflow number one in the

00:02:47
second image input slot. So instead of uploading a real reference image there, you can upload one of these skeleton images directly. Meanwhile, in workflow number two, you can upload any photo you want and it will automatically convert that photo into a skeleton pose and give you the output. Regarding which models you should place here, I've written all the details in this note box and I'm also showing it visually here again so you can clearly see which models need to go into which nodes. For example, for this

00:03:16
node, you must download the main Q imageit 259 model. You can either use the lightweight version or the original full model. The GGF version is for computers that are a bit weaker because these are the lighter versions of the QN model. If you want to download the original full model, you absolutely need a powerful GPU, 24 GB or 32 GB VRAM. Even with a 16 GB GPU, you can somehow use the original model, but the process of generating photos will become very slow. For these models, you simply click

00:03:47
on this button and start the download. It opens this page and here you see four models. The two at the bottom are not relevant. They are older QNage models. What we want is the new QN IET 259 model, which is the plus version of QN IE. You should download one of the top two. If your GPU has 32 GB VRAM or more, you can download the first one. But if you have 24 GB VRAM, you can use the second one, which is the FP8 version. Even on a 32 GB GPU, the first version runs a bit heavy because it is 40 GB in

00:04:20
size, which is larger than the VRAM capacity of your GPU. But your computer can also use some of your system RAM in order to load the model. Since I have 32 GB VRAM, I downloaded this model and placed it inside my workflow. Also, make sure to set this option to FB8 if you want your generation speed to be higher. But if you want the full quality, the maximum possible quality, you can set this option to default. In that case, it will use the full 40 GB. If you set it to the second option, FP8, it will use

00:04:49
half the size of the model. or you can directly download the FP8 version itself. And then it doesn't matter which of these two options you select because the model itself is FP8 by default and already compressed. The GGF version is downloaded from this link. When you go there, you'll see that it has different versions. For example, if you have an 8 GB GPU, you can use the Q2 model because its size is less than 8 GB. So, it won't put too much pressure on your GPU and you can run this model, but the higher

00:05:16
you go, the stronger GPU you need. For example, if you have a 16 GB GPU, you can use the Q5 version or Q5M, which is a little smaller than Q5L. If you have a 24 GB GPU, you can even use the Q8 version. This one here is the text encoder, and it goes here in this node. You download it from this link. This one is for the VAE. And this last option here is the Lightning Lura, which allows you to use eight steps instead of 20 steps. When I click on this to download the Laura, you can see there are a few

00:05:45
different versions of it. My suggestion is that you don't go for the four-step version and instead use the eightstep versions. In this section, you can see that we have different models for eight steps. If you downloaded the original QNage model BF-16, then your Laura should also be BF16. But if you're using the GGF versions or FP8, then you should use the Laura versions that don't have BF-16 in their name. Here, I've explained clearly where each one should be placed. Put each file into its own

00:06:12
correct folder. Now here you can easily load each of these models. If the models you downloaded and placed in their folders don't show up in your conf UI, just press the R key on your keyboard once and your Confi will refresh. After refreshing, the models will appear here. After you've downloaded everything, place them into their specific folders and hit R in confi. You still need to select each model one by one. Even if you see their names showing up here, you must select them again. The same goes

00:06:38
for the next nodes. Now we have two more workflows. Workflow number three and workflow number four. In workflow number three, we can apply a pose to a whole group of images with just one click. Let's say I have a set of eight portrait photos of different people here, and I want all the women in these eight photos to take on the same pose. For the pose, I've used one from that 200 pose skeleton pack. You can simply drag and drop it here into the workflow. So, how did I give these eight photos as inputs

00:07:04
to the workflow? It's really simple. Just save all the images you want to use in a single folder. Then go to that folder, click here on this section, copy the folder path, and paste it here into this node inside workflow number three. Once you run workflow number three, all of those images with just one click will automatically adopt the pose of that skeleton. You no longer need to upload each image one by one or run the process separately for each photo. Even if you have 100 images, the workflow will start

00:07:34
processing them one by one automatically, applying the same pose to all of them. You can see how much this speeds up your work, especially if you're dealing with large batches. For example, in online shops where you might want to show the same clothing item on multiple models in the same pose. This workflow can help a lot in those cases. In workflow number four, we have the opposite setup. Instead of workflow number three where we had several model photos, several character photos, here you can give it one character image as

00:08:08
input and then feed it a large number of skeleton poses. It will generate this same person across all those poses for you. You can see I have one input image here which is my character. It can even be an anime, cartoon, 3D or any style character. All you need to do is paste the folder path where I've saved those skeletons into this field here. For example, let's create a folder together. I'll go to the web website, find the 200 post file on the left sidebar, and click it. The downloadable files are here. I just need

00:08:38
to download this file. Now, I'll extract it from the compressed archive and open the folder. I'll create a new folder and then copy any poses I like or need into this new folder. Just like this. Now, I'll copy the path of this folder from here. go to workflow number four and paste it into this field. Then I'll click run. You'll see how precisely it applies each pose one by one to the character. It processes them in order, nice and clean. You can click on each result and view

00:09:32
the full image. These small preview images you're seeing here aren't a single file containing multiple pictures. Each of them is actually a separate image that's been saved individually inside your output folder. So, where is your output folder located? It's simple. Just go to your main Confy UI directory, then open the output folder, and you'll see that all the generated images are stored there separately. You don't need to manually save them one by one. You can just click

00:09:58
on any of them, and by pressing this option here, it will move to the next image, allowing you to browse through them one by one. You'll see that each image has taken on its corresponding pose in order. It's an amazing tool. It lets you do all of this very quickly and saves you a lot of time. And if you're working with a large number of images, workflows number three and four will be extremely useful for you. It's also interesting to know that Nano Banana doesn't support these skeleton pose

00:10:22
inputs. You actually have to describe the pose inside your prompt for it to try to replicate it. But QN Image Edit Plus is one of the best tools for changing your character's poses with high quality results. Workflows number one and two are completely free, while workflows number three and four are exclusive to my subscribers on WP and Booie. If you're already a subscriber, you can go to the link in the description, Access Swap or Booie, and download them from there. It's super easy. And if you're not a subscriber

00:10:48
yet, you can subscribe. And as a subscriber, you'll get access to all my previous workflows that I've uploaded to WP and showcased on YouTube. Basically, everything since I started my channel about a year ago. You can download any VIP or paid workflow completely for free once you subscribe. Plus, from the day you subscribe and for 30 days after that, any new workflow I upload will also be available to you for free. Now, how do we run this workflow on cloud GPUs? My recommendation is using Rumpod

00:11:16
because in my experience, it has fewer bugs and errors, almost none at all. And it also offers a very userfriendly interface. I've placed the link in the description. Just click on it and open the romp website first. If you don't have a Rampad account, go ahead and sign up. You can use your Google account or your email. Also, adding credit is a lot like paying on other online websites. You can use a credit card and depending on your location, bank transfer and crypto options may be available. So, I

00:11:49
don't explain it in very details, you can do it. And I think it's very simple to sign up in a website and add credit to it. After that we will start creating a network volume. On the manage menu click on storage. Then click on new network volume. We will choose a data center to set up our network volume. The most important thing is to pick a data center that has the GPUs you will use for your installation. Use an easy way to do this is to just click the GPU you want, the name of the GPU you want, and the available data

00:12:28
centers will be filtered for you. After you've picked your data center, let's give your network volume a name. Then decide on the this size for Comfy UI. 50 GB is a great place to start and you can always increase it later. When you're ready, just click create network volume. The new empty disc will appear in your list of network storage buckets. Simply click on it and then click deploy pod with volume. Now select the GPU you want to use to start the installation. In this example, we'll be

00:13:16
using an RTX 1590. And the next step is to select your template. Click the change template button here. Type kn space conf. And you have two options here. If you use 1490 GPU, select this one. And if you use 1590 GPU, select this one. Okay. When you're ready, just click on deploy on demand. Your new pod is created and its control panel is now visible. Head over to the logs to watch the installation. Comfy UI is installing onto your network desk. A process that usually takes 15 to 30 minutes. This is

00:14:00
a one-time setup for any subsequent pods. Comfy UI will start up in just a few seconds. You'll know the installation is finished when a message appears telling you to go to the GUI on port 8188. From there, just click on connect at the top and you can jump right into Comfy UI using port 8188. And just like that, you're ready to start using Comfy UI. This template installs a clean version of Comfy UI without any models or custom nodes, but it does include the Comfy UI manager and you can use it to download the models

00:14:41
and install the custom nodes you need to run for this workflow. Now you can easily drag and drop our workflow into this config UI. As before you can select manager and click on install missing custom nodes and do the same which I explained at the beginning of this video. Then for downloading the models and putting them on the proper path, the easiest way is that use this node. Double click on your confi interface and search for URL. Then select download from URL. And if you pay attention in the workflow, I prepared all download

00:15:44
links for the models you need to run this workflow. Simply come to this node which I put all the links. Click on it. And you see the links are here. For example, I want to download this one for my infinite tag model. I select the link like this and copy it. Then paste it in the URL section here. And in the second row, you should choose the path. You should choose the directory you want this model to be placed. I also mentioned the directory you need to put this model on it. Again, come to this node. And as you can see

00:16:34
for infinite talk, you need to use models folder and unit folder. Then go back to the download from URL node and select the saved diir. Click on it and you can see a drop-down menu appears. Select unit and up here click on play button. It would automatically download this model and put it in the directory you selected. Just like that. Do it for all models. After downloading all models, you need to refresh your confi. Press R on your keyboard or if it doesn't work click on address bar on your browser and hit enter. It will

00:17:16
refresh your conf UI interface. Now one by one select the models you have downloaded in all these red colored nodes. Just like that and you're ready to use this workflow. Thanks for watching. I'll see you in the next video.

