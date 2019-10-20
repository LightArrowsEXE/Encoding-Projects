import ocsuite as ocs
import lvsfunc as lvf
oc = ocs.OC()


path = r'BDMV/Vol 1/BDROM/BDMV/STREAM/00001.m2ts'
src = lvf.src(path)

if __name__ == "__main__":
    oc.eztrim(src, [(24, -24)], path[:-4]+"wav", "CaseFilesBD_01_cut.wav")