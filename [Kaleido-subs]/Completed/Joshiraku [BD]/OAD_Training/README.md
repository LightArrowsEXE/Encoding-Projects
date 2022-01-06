# Joshiraku OAD model training

Prior to finding out there was, in fact, a BD source for the OAD,
I had trained a model to upscale it.
Here are the files for that in case anyone wants to try it out on other,similar cases
where there's (presumably) a DVD-only episode of a show,
but you have BDs and DVDs for at least 1 cour worth of episodes to act as the dataset.

You must first make sure that everything lines up perfectly.
This means downscaling the BD to 486p and cropping it until it matches the DVDs,
and depending on whether you want to do a 1x model or a 2x model,
translate that to how it's supposed to look when cropped at 960p.
You must also make sure the colourspaces are all set up properly,
and that you take those into account when training the model.
Far too often do people cock up the colourspaces and think it makes the image looks "better",
when you're really just displaying it wrong.
See it all the time in these Model Upscaling circles,
and they never seem to learn that this is not what you're supposed to do.

I also recommend pre-filtering the BD.
You want it to look as good as possible,
so reducing the amount of compression artefacting and mastering defects goes a long way.
