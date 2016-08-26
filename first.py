#goal is translatedocument into vretor 


import numpy


file = open('/home/chang/my/test.txt')
dic = {'a':0,'b':1,'c':3,'d':4,'e':5,'f':6,'g':7,'h':8,'i':9,'j':10,'k':11,'l':12,'m':13,'n':14,'o':15,'p':16,'q':17,'r':18,'s':19,'t':20,'u':21,'v':22,'w':23,'x':24,'y':25,'z':26,'0':27,'1':28,'2':29,'3':30,'4':31,'5':32,'6':33,'7':34,'8':35,'9':36}
data = file.read()
data = data.replace(' ','')
data = data.replace('\n','')
data = data.strip(',./<>?:;"[]')
word_list = list(data)
word_list = word_list[1:100]
vec = []


str_dic='abcdefghijklmnopqrstuvwxyz0123456789'
for word in word_list:
	if word in str_dic:
		vec.append( dic[word] )
print vec

