# -*- coding:utf-8 -*-


try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import sys
from collections import defaultdict
from math import sqrt
import os

def lenOfSamePrefix(str1,str2):
    """
    :param str1:
    :param str2:
    :return:
    """
    i=0
    while i<len(str1) and i<len(str2):
        if(str1[i]==str2[i]):
            i=i+1
        else:
            return i
    return i

def eta_mean(a,b):
    if a == 0 and b == 0:
        return 0
    else:
        return 2.0 * a * b /(a*a + b*b)

def thres_mean(f,r,l,p):
    return sqrt(f)/(1.0/r + 1.0/l) * p

def countWord(line,wordDict):
    """
    :param line:
    :param wordDict:
    :return:
    """
    for i in range(0,len(line)):
        word=line[i:]
        if word in wordDict:
            wordDict[word]=wordDict[word]+1
        else:
            wordDict[word]=1


class Newword:
    def __init__(self, config_file):
        cf = configparser.ConfigParser()
        cf.read(config_file)

        self.n_freq=cf.getint("newword", "n_freq")
        self.n_pmi=float(cf.get("newword", "n_pmi"))
        self.n_av=cf.getint("newword", "n_av")
        self.n_eta=float(cf.get("newword", "n_eta")) # 2ab/(a^2+b^2)
        self.n_size=cf.getint("newword", "n_size") #
        self.n_gram=cf.getint("newword", "n_gram") #
        self.n_threshold=float(cf.get("newword", "n_threshold"))
        print("n_freq:", self.n_freq)
        print("n_pmi:", self.n_pmi)
        print("n_av:", self.n_av)
        print("n_eta:", self.n_eta)
        print("n_size:", self.n_size)
        print("n_gram:", self.n_gram)

        file_punct=cf.get("dictionary", "punct")
        self.filecode=cf.get("default", "filecode")
        self.punct_set=set(w.strip() for w in  open(file_punct, 'r',  encoding=self.filecode)) if file_punct is not None else set()
        self.punct_set.add(" ")
        self.punct_set.add("\t")
        self.statresults = dict()
        self.alnum_dict = defaultdict(int)


    def splitLine(self, line, wordDict, alnum_dict, reverse):
        bPos=0
        for i in range(0,len(line)):
            if line[i] in self.punct_set:
                strng=line[bPos:i]
                if strng.encode(self.filecode).isalnum():
                    if not reverse:
                        alnum_dict[strng]+=1
                else:
                    countWord(strng, wordDict)
                #print(strng)
                bPos=i+1
        if bPos<len(line):
            strng=line[bPos:]
            #if strng.isalnum():
            if strng.encode(self.filecode).isalnum():
                if not reverse:
                    alnum_dict[strng]+=1
            else:
                countWord(strng, wordDict)
            #print(strng)
    def splitLine1(self, line, nLen, wordDict, alnum_dict):
        prePos = -1
        i = 0
        while i< len(line):
            if line[i] in self.punct_set:
                if i!= prePos + 1:
                    for j in range(0, i - prePos):
                        t = i - prePos -1 if i- prePos -1 <= j + nLen else j + nLen
                        strng=line[prePos + 1 +j: prePos + 1 + t]
                        countWord(strng, wordDict)
                        #print(strng)
                prePos = i
            i+=1
        if i != prePos + 1:
            for j in range(0, i - prePos):
                t = i - prePos -1 if i- prePos -1 <= j + nLen else j + nLen
                strng=line[prePos + 1 +j: prePos + 1 + t]
                countWord(strng, wordDict)
                #print(strng)

    def getWordFreq(self, modef,reverse, wordDict,PList,LList,bLen, eLen):
        nlr= reverse
        for i in range(bLen,eLen):
            j=0
            while j<len(PList) and len(PList[j])<i:
                j+=1
            if j==len(PList):
                continue
            xWord=PList[j][:i]
            if(nlr==2):
                xWord=xWord[::-1]
            xCount=wordDict[PList[j]]
            if len(PList[j])==i:
                xVariety=wordDict[PList[j]]
            else:
                xVariety=1
            for k in range(j,len(LList)):
                if LList[k]>=i:
                    xCount+=wordDict[PList[k+1]]
                    if LList[k]==i:
                        if len(PList[k+1])==i:
                            xVariety+=wordDict[PList[k+1]]
                        else:
                            xVariety+=1
                else :
                    if len(xWord)==i:
                        if modef==True:
                            self.statresults.setdefault(xWord,{})[1]=xCount
                        self.statresults.setdefault(xWord,{})[4]=i
                        self.statresults.setdefault(xWord,{})[nlr]=xVariety
                    xCount=wordDict[PList[k+1]]
                    if len(PList[k+1])==i:
                        xVariety=wordDict[PList[k+1]]
                    else:
                        xVariety=1
                    xWord=PList[k+1][:i]
                    if(nlr==2):
                        xWord=xWord[::-1]
            if len(xWord)==i:
                if modef==True:
                    self.statresults.setdefault(xWord,{})[1]=xCount
                    self.statresults.setdefault(xWord,{})[4]=i
                self.statresults.setdefault(xWord,{})[nlr]=xVariety

    def yieldItem(self):
        for sr in self.statresults:
            sr_dict = self.statresults[sr]
            sr_eta_mean = eta_mean(sr_dict[2], sr_dict[3])
            if sr_dict[4]<self.n_size or sr_dict[1] < self.n_freq or min(sr_dict[2], sr_dict[3]) < self.n_av or sr_eta_mean < self.n_eta:
                continue
            tmp_mi = 0
            min_pmi = 999
            for j in range(1, sr_dict[4]):
                tmp_mi = sr_dict[1]/(self.statresults[sr[:j]][1]*self.statresults[sr[j:]][1])
                if min_pmi > tmp_mi:
                    min_pmi = tmp_mi
            sr_threshold = thres_mean(sr_dict[1], sr_dict[3], sr_dict[2], min_pmi)
            if sr_threshold > self.n_threshold:
                yield sr, sr_dict[1], sr_dict[2], sr_dict[3], min_pmi, sr_eta_mean, sr_threshold
        for sr in self.alnum_dict:
            if self.alnum_dict[sr] >= self.n_freq:
                yield sr, self.alnum_dict[sr], self.alnum_dict[sr], self.alnum_dict[sr], self.n_pmi, self.n_eta, self.n_threshold

    def readCorpus(self, file_corpus, wordDict, reverse=False):
        with open(file_corpus,'r', encoding=self.filecode,errors='ignore') as in_file:
            for line in in_file:
                line = line.strip().lower()
                if reverse:
                    line = line[::-1]
                self.splitLine(line,  wordDict, self.alnum_dict, reverse)

    def processNagao(self, file_corpus):
        wordDict = dict()
        self.readCorpus(file_corpus, wordDict)
        pList=list(sorted(wordDict))
        lList = [lenOfSamePrefix(pList[i],pList[i+1]) for i in range(0, len(pList)-1)]
        self.getWordFreq(True,3,wordDict,pList,lList,1,self.n_gram)
        wordDict = dict()
        self.readCorpus(file_corpus, wordDict, True)
        pList=list(sorted(wordDict))
        lList = [lenOfSamePrefix(pList[i],pList[i+1]) for i in range(0, len(pList)-1)]
        self.getWordFreq(False,2,wordDict,pList,lList,1,self.n_gram)
        del wordDict, pList, lList
        return self.yieldItem()
if __name__ == "__main__":
    if len(sys.argv)<3:
        print("Usage: python3 input_file output_file [newword.conf]")
        exit()
    file_corpus = sys.argv[1]
    file_output = sys.argv[2]
    file_config = sys.argv[3] if len(sys.argv) >3 else "newword.utf8.conf"
    file_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),file_config)
    newword = Newword(file_config)
    with open(file_output, 'w',encoding=newword.filecode) as f:
        for word,freq,l,r,pmi,eta, thres in newword.processNagao(file_corpus):
            f.write("%s,%s,%s,%s,%s,%s,%s\n"%(word,freq,l,r,pmi,eta,thres))

