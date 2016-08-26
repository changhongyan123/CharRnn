#mmodel
import pandas as pd

from keras.models import Model
from keras.layers import Dense, Activation, Flatten, Input, Dropout, MaxPooling1D, Convolution1D
from keras.layers import LSTM, Lambda, merge
from keras.layers import Embedding, TimeDistributed
import numpy as np
import tensorflow as tf
import re
from keras import backend as K
import keras.callbacks
import sys
import os


def binarize(x):
	 return tf.to_float(tf.one_hot(x, 71, on_value=1, off_value=0, axis=-1))#depth is 71.if x is (m,n),the output is m*sz*n,x is 1,other is 0.



def binarize_outshape(in_shape):
    return (in_shape[0], in_shape[1], 71)


def max_1d(X):
    return K.max(X, axis=1)



def striphtml(s):
    p = re.compile(r'<.*?>')
    return p.sub('', s)


def clean(s):
    return re.sub(r'[^\x00-\x7f]', r'', s)#maybe lower

total = len(sys.argv)
cmdargs = str(sys.argv)

print ("Script name: %s" % str(sys.argv[0]))
checkpoint = None
if len(sys.argv) == 2:
    if os.path.exists(str(sys.argv[1])):
        print ("Checkpoint : %s" % str(sys.argv[1]))
        checkpoint = str(sys.argv[1])

#load data
data = pd.read_csv("/home/chang/my/data/train.tsv", header=0, delimiter="\t", quoting=3)
txt = ''
docs = []
sentences = []
sentiments = []

for cont, sentiment in zip(data.review, data.sentiment):#(review,sentiment)
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', clean(striphtml(cont)))#split useless word,contains many sentences
    sentences = [sent.lower() for sent in sentences]#This sentences split by signal.
    docs.append(sentences[:3])#every review contain how much sentence
    sentiments.append(sentiment)
docs=docs[:3]#doc contains how much review

num_sent = []
for doc in docs:#loop in every review
    num_sent.append(len(doc))#record the length of sent(contain how much character)
    for s in doc:#loop in each review(str)
        txt += s#This contains all character in the file(all review)
print txt
chars = set(txt)#how many character be used.

print('total chars:', len(chars))
char_indices = dict((c, i) for i, c in enumerate(chars))#number and character. 
indices_char = dict((i, c) for i, c in enumerate(chars))

print('Sample doc{}'.format(docs[2]))#output one review

maxlen = 100
max_sentences = 5

X = np.ones((len(docs), max_sentences, maxlen), dtype=np.int64) * -1#This is a matrix all is -1,review_num*max_sentence_maxlen
y = np.array(sentiments)#sentiment is array.

for i, doc in enumerate(docs):#i==review_index,doc==review
    for j, sentence in enumerate(doc):#j==sentene_index,sentence==sentence
        if j < max_sentences:
            for t, char in enumerate(sentence[-maxlen:]):#from the last:extract the maxlen character.and t==character_index,char == character
                X[i, j, (maxlen-1-t)] = char_indices[char]#X(i,j,k)means :the index of character appear in the i_th review,and   k_th character.

print('Sample X:{}'.format(X[2, 2]))#output one review
print('y:{}'.format(y[2]))#the 2_th review's sentiment

ids = np.arange(len(X))
np.random.shuffle(ids)

# shuffle
X = X[ids]
y = y[ids]

X_train = X[:20000]
X_test = X[22500:]

y_train = y[:20000]
y_test = y[22500:]


def char_block(in_layer, nb_filter=[64, 100], filter_length=[3, 3], subsample=[2, 1], pool_length=[2, 2]):
    block = in_layer
    for i in range(len(nb_filter)):

        block = Convolution1D(nb_filter=nb_filter[i],
                              filter_length=filter_length[i],
                              border_mode='valid',
                              activation='relu',
                              subsample_length=subsample[i])(block)
        # block = BatchNormalization()(block)
        block = Dropout(0.1)(block)
        if pool_length[i]:
            block = MaxPooling1D(pool_length=pool_length[i])(block)

    block = Lambda(max_1d, output_shape=(nb_filter[-1],))(block)
    block = Dense(128, activation='relu')(block)
    return block




max_features = len(chars) + 1#max_character_set
char_embedding = 40

document = Input(shape=(max_sentences, maxlen), dtype='int64')#input layer

in_sentence = Input(shape=(maxlen,), dtype='int64')#input layers
#problem here!!!!!why??

embedded = Lambda(binarize, output_shape=binarize_outshape,input_shape=in_sentence.shape)#embedded is lamdad layer,binarize extract the output last layer.



block2 = char_block(embedded(in_sentence), [100, 200, 200], filter_length=[5, 3, 3], subsample=[1, 1, 1], pool_length=[2, 2, 2])
block3 = char_block(embedded, [200, 300, 300], filter_length=[7, 3, 3], subsample=[1, 1, 1], pool_length=[2, 2, 2])


sent_encode = merge([block2, block3], mode='concat', concat_axis=-1)
sent_encode = Dropout(0.4)(sent_encode)

encoder = Model(input=in_sentence, output=sent_encode)
encoded = TimeDistributed(encoder)(document)

lstm_h = 80
forwards = LSTM(lstm_h, return_sequences=False, dropout_W=0.15, dropout_U=0.15,
                consume_less='gpu')(encoded)
backwards = LSTM(lstm_h, return_sequences=False, dropout_W=0.15, dropout_U=0.15,
                 consume_less='gpu', go_backwards=True)(encoded)

merged = merge([forwards, backwards], mode='concat', concat_axis=-1)
output = Dropout(0.3)(merged)
output = Dense(1, activation='sigmoid')(output)

model = Model(input=document, output=output)


if checkpoint:
    model.load_weights(checkpoint)


file_name = os.path.basename(sys.argv[0]).split('.')[0]

check_cb = keras.callbacks.ModelCheckpoint('checkpoints/'+file_name+'.{epoch:02d}-{val_loss:.2f}.hdf5', monitor='val_loss',
                                           verbose=0, save_best_only=True, mode='min')

earlystop_cb = keras.callbacks.EarlyStopping(monitor='val_loss', patience=5, verbose=0, mode='auto')

model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

model.fit(X_train, y_train, validation_data=(X_test, y_test), batch_size=10,
          nb_epoch=30, shuffle=True, callbacks=[check_cb, earlystop_cb])
