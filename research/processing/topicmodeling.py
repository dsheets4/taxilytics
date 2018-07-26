import os
import re
import logging
import sys

from gensim import corpora, models  # , similarities
import numpy as np

import util


logger = logging


class Library(object):

    def __init__(self, doclib, cache_dir, stoplist=(), min_freq=2, regen=False):
        if regen:
            logger.info('Forcing regeneration of corpora')

        if cache_dir is None:
            self._create(doclib, stoplist, min_freq)
        else:
            dict_cache_file = os.path.join(cache_dir, 'dictionary.dict')
            corpus_file = os.path.join(cache_dir, 'corpus_bow.mm')
            if (os.path.isfile(dict_cache_file) and os.path.isfile(corpus_file) and
                    not regen):
                logger.info('Loading corpora from {}'.format(cache_dir))
                self.dictionary = corpora.Dictionary.load(dict_cache_file)
                self.corpus = corpora.MmCorpus(corpus_file)
            else:
                logger.info('Creating corpora in {}'.format(cache_dir))
                self._create(doclib, stoplist, min_freq)
                self.dictionary.save(dict_cache_file)
                corpora.MmCorpus.serialize(
                    corpus_file, self.corpus, self.dictionary)

    def _create(self, doclib, stoplist, min_freq):
        if callable(doclib):
            logger.info('Calling to create document library')
            doclib = doclib()

        self.dictionary = corpora.Dictionary(traj for traj in doclib)

        # remove stop words and words that appear only once
        if isinstance(stoplist, str):
            with open(stoplist, 'r') as slf:
                stoplist = set(re.split(r'[\w\n]', slf.read()))

        stop_ids = [self.dictionary.token2id[stopword] for stopword in stoplist
                    if stopword in self.dictionary.token2id]
        once_ids = [tokenid for tokenid, docfreq in self.dictionary.dfs.items()
                    if docfreq < min_freq]
        self.dictionary.filter_tokens(stop_ids + once_ids)

        # Final resulting resources.
        self.dictionary.compactify()
        self.corpus = [self.dictionary.doc2bow(doc) for doc in doclib]


class TopicModel(object):

    def __init__(self, impl='MalletLda', **kwargs):

        # Finally, we create the topic model and let 'r rip!
        class_name = '_{}'.format(impl)
        model_class = getattr(sys.modules[__name__], class_name)
        kwargs, unused, _ = util.filter_kwargs(model_class, kwargs)
        if len(unused) > 0:
            logger.warning('Topic model "{}" has unused arguments: {}'.format(
                impl,
                unused
            ))

        regen = kwargs.get('regen', None)
        if regen:
            logger.info('Forcing regeneration of topic model')

        self.model = model_class(**kwargs)

    def __getattr__(self, name):
        return getattr(self.model, name)

    def __getitem__(self, doclib):
        return self.model[doclib]


class _BaseTopicModel(object):

    def __init__(self, library, cache_dir=None, regen=False):
        self._library = library
        self.cache_dir = cache_dir
        self.regen = regen

    def __getitem__(self, doclib):
        inferred_corpus = []
        for doc in enumerate(doclib):
            inferred_corpus.append(
                self.model[self.library.dictionary.doc2bow(doc)]
            )
        return inferred_corpus

    def __getattr__(self, name):
        return getattr(self.model, name)

    @property
    def library(self):
        if not isinstance(self._library, Library):
            self._library = Library(
                doclib=self._library,
                cache_dir=self.cache_dir,
                regen=self.regen
            )
        return self._library


class _MalletLda(_BaseTopicModel):

    def __init__(self,
                 num_topics, library,
                 cache_dir='./', prefix='mallet_',
                 iterations=1000,
                 mallet='../3rdparty/mallet/bin/mallet',
                 regen=False):

        super(_MalletLda, self).__init__(library, cache_dir, regen)

        model_filename = os.path.join(cache_dir, 'mallet.lda')
        prefix = os.path.join(cache_dir, prefix)
        if os.path.isfile(model_filename) and not regen:
            logger.info('Loading MALLET LDA from {}'.format(cache_dir))
            self.model = models.wrappers.LdaMallet.load(model_filename)
            # Allows migrating the topic model.
            self.model.prefix = prefix
            self.model.mallet_path = mallet
        else:
            logger.info('Creating MALLET LDA in {}'.format(cache_dir))
            self.model = models.wrappers.LdaMallet(
                mallet,
                self.library.corpus,
                id2word=self.library.dictionary,
                num_topics=num_topics,
                iterations=iterations,
                prefix=prefix
            )
            self.model.save(model_filename)

    def __getitem__(self, doclib):
        corpus_to_infer = []
        for doc in doclib:
            corpus_to_infer.append(self.library.dictionary.doc2bow(doc))
        return self.model[corpus_to_infer]


class _GensimLda(_BaseTopicModel):

    def __init__(self,
                 num_topics, library,
                 cache_dir='./',
                 iterations=500, alpha='auto',
                 regen=False):

        super(_GensimLda, self).__init__(library, cache_dir, regen)

        if not alpha == 'auto':
            # [float(alpha) / num_topics] * num_topics
            alpha = np.asarray([float(alpha)] * num_topics)

        model_filename = os.path.join(cache_dir, 'model.lda')
        if os.path.isfile(model_filename) and not regen:
            logger.info('Loading gensim LDA from {}'.format(cache_dir))
            self.model = models.LdaModel.load(model_filename)
        else:
            logger.info('Creating gensim LDA in {}'.format(cache_dir))
            self.model = models.LdaModel(
                self.library.corpus,
                id2word=self.library.dictionary,
                num_topics=num_topics,
                iterations=iterations,
                alpha=alpha
            )
            self.model.save(model_filename)


class _GensimTfIdf(_BaseTopicModel):

    def __init__(self, library, cache_dir, regen=False):

        super(_GensimTfIdf, self).__init__(library, cache_dir, regen)

        tfidf_model_filename = os.path.join(cache_dir, 'model.tfidf')
        if os.path.isfile(tfidf_model_filename) and not regen:
            logger.info('Loading gensim TF/IDF from {}'.format(cache_dir))
            self.model = models.TfidfModel.load(tfidf_model_filename)
        else:
            logger.info('Creating gensim TF/IDF in {}'.format(cache_dir))
            self.model = models.TfidfModel(
                self.library.corpus,
                normalize=True
            )
            self.model.save(tfidf_model_filename)


class _GensimLsi(_BaseTopicModel):

    def __init__(self, num_topics, library, cache_dir, regen=False):

        super(_GensimLsi, self).__init__(library, cache_dir, regen)

        self.tfidf = _GensimTfIdf(library, cache_dir)

        tfidf_corpus_filename = os.path.join(cache_dir, 'corpus_tfidf.mm')
        if os.path.isfile(tfidf_corpus_filename) and not regen:
            logger.info('Loading gensim LSI from {}'.format(cache_dir))
            self.corpus_tfidf = corpora.MmCorpus(tfidf_corpus_filename)
        else:
            logger.info('Creating gensim LSI in {}'.format(cache_dir))
            self.corpus_tfidf = self.tfidf[self.library.corpus]
            corpora.MmCorpus.serialize(
                tfidf_corpus_filename,
                self.corpus_tfidf,
                self.library.dictionary
            )

        model_filename = os.path.join(cache_dir, 'model.lsi')
        if os.path.isfile(model_filename):
            self.model = models.LsiModel.load(model_filename)
        else:
            self.model = models.LsiModel(
                self.corpus_tfidf,
                id2word=self.library.dictionary,
                num_topics=num_topics
            )
            self.model.save(model_filename)
