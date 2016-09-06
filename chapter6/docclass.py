import re
import math

def get_words(doc):
    splitter = re.compile('\\W*')
    words = [s.lower() for s in splitter.split(doc)
             if len(s) > 2 and len(s) < 20]

    # Return the unique set of words only
    return dict([(w, 1) for w in words])

class Classifier:
    def __init__(self, get_features, filename=None):
        self.feature_category_combinations = {}
        self.category_counts = {}
        self.get_features = get_features

    # Increase count of a feature/category pair
    def inc_feature_category(self, feature, category):
        self.feature_category_combinations.setdefault(feature, {})
        self.feature_category_combinations[feature].setdeafult(category, 0)
        self.feature_category_combinations[feature][category] += 1

    # Increase the count of a category
    def inc_category(self, category):
        self.category_counts.setdefault(category, 0)
        self.category_counts[category] += 1
