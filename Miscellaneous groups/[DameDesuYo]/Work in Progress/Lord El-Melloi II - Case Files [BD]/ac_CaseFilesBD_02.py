import ocsuite as ocs
import lvsfunc as lvf
oc = ocs.OC()


path = r'BDMV/[BDMV] Lord El-Melloi II-sei no Jikenbo ~Rail Zeppelin Grace Note~ [Vol.02]/BDROM/BDMV/STREAM/00000.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    oc.eztrim(src, [(24, -24)], path[:-4]+"wav", "CaseFilesBD_02_cut.wav")
