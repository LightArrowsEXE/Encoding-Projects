import vapoursynth as vs
import lvsfunc as lvf
import fvsfunc as fvf
core = vs.core

MV = lvf.src(r"『灰と幻想のグリムガル』CD-BOX2「Luster」(K)NoW_NAME《アニメMV Short Ver.》-2vu9bdNQaW8.mkv")
MV_endcard = MV[3877:]
mv = MV

src_11 = lvf.src(r"F:\Portfolio\[Kaleido-subs]\Hai to Gensou no Grimgar\parts\!scripts\[BDMV][アニメ] 灰と幻想のグリムガル\[BDMV][アニメ][160817] 灰と幻想のグリムガル Vol.6\BDROM\BDMV\STREAM\00003.m2ts")
src_12 = lvf.src(r"F:\Portfolio\[Kaleido-subs]\Hai to Gensou no Grimgar\parts\!scripts\[BDMV][アニメ] 灰と幻想のグリムガル\[BDMV][アニメ][160817] 灰と幻想のグリムガル Vol.6\BDROM\BDMV\STREAM\00007.m2ts")

src = src_11[10730:10850]+src_11[10501:10512]+src_11[10512:10528]+src_11[10531:10545]+src_11[11686:11724]+src_11[12981:13009]+src_11[14773:14803]+src_11[13851:13867]+src_11[13385:13405]+src_11[13432:13487]+src_11[14249:14261]+src_11[14267:14282]+src_11[14317:14339]+src_11[15194:15225]+src_11[15236:15261]+src_11[15345:15361]+src_11[15369:15411]+src_11[15459:15482]+src_11[15486:15508]+src_11[15532:15551]+src_11[15603:15658]+src_11[16798:16914]+src_11[16979:17038]+src_11[17063:17111]+src_11[17939:18179]+src_11[18190:18233]+src_11[18291:18441]+src_11[18542:18622]
#23355 Ep11

saku1 = src_11[3045:3135]+src_11[3271:3319]
saku2 = src_11[23756:24252]
saku3 = src_11[25270:25759]
saku4 = src_11[26403:26487]+src_11[26511:26811]+src_11[26882:26945]+src_11[27373:27407]+src_11[27499:27955]
saku5 = src_11[30941:31121]
saku6 = src_12[22322:22585]+src_12[22694:23318]
saku7 = src_12[26204:26490]+src_12[26684:26852]
saku8 = src_12[29214:29502]+src_12[30288:30640]+src_12[30672:30716]+src_12[30752:30851]+src_12[31000:31356] #31356
saku9 = src_12[32708:32810]+src_12[32818:33042]+src_12[33252:33564]
saku10= src_12[23318:24007]+src_12[24250:24316]
sakuga = core.resize.Spline36(saku10, 848, 480)
comp = lvf.stack_compare(mv, src, height=480)
comp.set_output()