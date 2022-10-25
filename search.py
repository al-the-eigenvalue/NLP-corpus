import csv
import random
import copy
import spacy
from spacy.matcher import Matcher
from spacy.tokens import Span
from spacy.language import Language
from spacy import displacy
from pymorphy2 import MorphAnalyzer

class Search:

    global morph
    morph = MorphAnalyzer()

    def __init__(self):
        self.nlp = spacy.load("ru_core_news_sm")
        self.nlp.add_pipe("pos_postprocessor", after="ner")
        self.matcher = Matcher(self.nlp.vocab)

        self.labels = ["ADJ", "ADP", "ADV", "CCONJ", 
                    "CONV", "DET", "INTJ", "NOUN", 
                    "NUM", "PART", "PRON", "PROPN", 
                    "PRT", "SCONJ", "VERB", "X"]

        self.colors = ["#a474dc", "#dcd0ff", "#e6a8d7", "#dbd7d2", 
                "#84c3be", "#3cb371", "#009a63", "#1e90ff", "#9d81ba", 
                "#badbad", "#bdecb6", "#a8e4a0", "#dad871", "#ffa343", 
                "#d6ae01", "#ffcf48", "#fde910", "#bfff00", "#7fff00", 
                "#76ff7a", "#00ff7f", "#54ff9f", "#bef574", "#b2ec5d", 
                "#ffff66", "#fddb6d", "#d1e231", "#ffff99", "#fae7b5", 
                "#ffbd88", "#deaa88", "#efaf8c", "#ffca86", "#b8b799", 
                "#ffb961", "#e9967a", "#ffa474", "#ee9086", "#ba7fa2", 
                "#b784a7", "#cf9b8f", "#cea262", "#7b917b", "#87cefa", 
                "#77dde7", "#80daeb", "#1fcecb", "#7fffd4", "#eceabe", 
                "#f5e6cb", "#efcdb8", "#fc89ac", "#e0b0ff", "#abcdef", 
                "#b0e0e6", "#ace5ee", "#ffdab9", "#ffcbbb", "#ffaacc", 
                "#d8bfd8"]

        with open("Corpus/mini_corpus.csv", encoding="utf-8") as raw_corpus:
            raw_corpus_data = list(csv.reader(raw_corpus, delimiter=';'))

        self.corpus_dict = dict()
        for row in raw_corpus_data:
            metadata = row[0] + ", " + row[1] + ", " + row[2]
            doc = self.nlp(row[3])
            sentences = []
            for sent in doc.sents:
                sentences.append(sent.as_doc())
            self.corpus_dict[metadata] = sentences   

    @Language.component("pos_postprocessor")
    def pos_postprocessor(doc):
        for token in doc:
            if "VerbForm=Conv" in token.morph:
                token.tag_ = "CONV" # деепричастие
                token.lemma_ = token.text
            elif "VerbForm=Part" in token.morph:
                token.tag_ = "PRT" # причастие
                analyzed = morph.parse(token.text)[0]
                try:
                    token.lemma_ = analyzed.inflect({"sing", "masc"})[0]
                except:
                    pass
            elif token.pos_ == "AUX":
                token.tag_ = "VERB"
        return doc

    def input_to_pattern(self, input):
        pattern = []
        tags = input.split(" ")
        for tag in tags:
            if not "+" in tag:
                if len(tag) > 0:
                    if tag[0] == "\"" and tag[-1] == "\"":
                        pattern.append({"TEXT": tag[1:-1]})
                    elif tag in self.labels:
                        pattern.append({"TAG": tag})
                    else:
                        pattern.append({"LEMMA": self.nlp(tag)[0].lemma_})
            else:
                subtags = tag.split("+")
                pattern.append({"LEMMA": self.nlp(subtags[0])[0].lemma_, "TAG": subtags[1]})
        return pattern

    def match(self, pattern, sentences):
        matcher = Matcher(self.nlp.vocab)
        if pattern:
            matcher.add("☆", [pattern])

        result_sents = []
        for sent in sentences:
            matches = matcher(sent)
            if matches:
                sent.ents = []
                spans = [Span(sent, start, end, label=match_id) for match_id, start, end in matches]
                filtered_spans = spacy.util.filter_spans(spans)
                remaining_spans = [span for span in spans if span not in filtered_spans]
                for span in spans:#filtered_spans:
                    sent.ents = list(sent.ents) + [span]
                result_sents.append(sent)

                while remaining_spans:
                    duplicate_sent = copy.copy(sent)
                    duplicate_sent.ents = []
                    for span in remaining_spans:
                        duplicate_sent.ents = list(duplicate_sent.ents) + [span]
                    result_sents.append(duplicate_sent)
                    filtered_spans = spacy.util.filter_spans(remaining_spans)
                    remaining_spans = [span for span in remaining_spans if span not in filtered_spans]

        return result_sents

    def search(self, input):
        htmls = []
        metadata = []
        color = random.choice(self.colors)
        for item in self.corpus_dict:
            result = self.match(self.input_to_pattern(input), self.corpus_dict[item])
            if result:
                metadata.append(item)
                htmls.append(displacy.render(result, style="ent", 
                            options={"colors": {"☆": color}}))
        indices = list(range(len(metadata)))
        if not indices: 
            indices.append(0)
            metadata.append("К сожалению, по запросу ничего не нашлось!")
            htmls.append("")
        return indices, metadata, htmls