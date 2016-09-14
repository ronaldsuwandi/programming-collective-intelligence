import re
import math


def get_words(doc):
    splitter = re.compile('\\W*')
    words = [s.lower() for s in splitter.split(doc)
             if len(s) > 2 and len(s) < 20]

    # Return the unique set of words only
    return dict([(w, 1) for w in words])


def sample_train(classifier):
    classifier.train('Nobody owns the water.', 'good')
    classifier.train('the quick rabbit jumps fences', 'good')
    classifier.train('buy pharmaceuticals now', 'bad')
    classifier.train('make quick money at the online casino', 'bad')
    classifier.train('the quick brown fox jumps', 'good')


class Classifier:
    def __init__(self, get_features, filename=None):
        self.feature_category_combinations = {}
        self.category_counts = {}
        self.get_features = get_features

    # Increase count of a feature/category pair
    def inc_feature_category(self, feature, category):
        self.feature_category_combinations.setdefault(feature, {})
        self.feature_category_combinations[feature].setdefault(category, 0)
        self.feature_category_combinations[feature][category] += 1

    # Increase the count of a category
    def inc_category(self, category):
        self.category_counts.setdefault(category, 0)
        self.category_counts[category] += 1

    # Number of times a feature has appeared in category
    def feature_count(self, feature, category):
        if feature in self.feature_category_combinations and \
                        category in self.feature_category_combinations[feature]:
            return float(self.feature_category_combinations[feature][category])
        return 0.0

    # Number of items in a category
    def category_count(self, category):
        if category in self.category_counts:
            return float(self.category_counts[category])
        return 0

    # Total number of items
    def total_count(self):
        return sum(self.category_counts.values())

    # List of all categories
    def categories(self):
        return self.category_counts.keys()

    def train(self, item, category):
        features = self.get_features(item)
        for feature in features:
            self.inc_feature_category(feature, category)

        # Increment count for this category
        self.inc_category(category)

    def feature_probability(self, feature, category):
        if self.category_count(category) == 0:
            return 0

        # Total number of times this feature apparead in this category divided by the total
        # number of items in this category
        return self.feature_count(feature, category) / self.category_count(category)

    def weighted_probability(self, feature, category, probability_fn, weight=1.0,
                             assumed_probability=0.5):
        prob = probability_fn(feature, category)

        # Count all number of times this feature has appeared in all categories
        total_appeared = sum(
            [self.feature_count(feature, category) for category in self.categories()])

        # Calculate the weighted average
        return ((weight * assumed_probability) + (total_appeared * prob)) / (
        weight + total_appeared)


class NaiveBayes(Classifier):
    def __init__(self, get_features):
        Classifier.__init__(self, get_features)
        self.thresholds = {}

    def document_probability(self, item, category):
        features = self.get_features(item)

        # Multiply the probabilities of all features together
        p = 1
        for feature in features:
            p *= self.weighted_probability(feature, category, self.feature_probability)

        return p

    def probability(self, item, category):
        p_category = self.category_count(category) / self.total_count()
        p_document = self.document_probability(item, category)
        return p_document * p_category

    def set_threshold(self, category, threshold):
        self.thresholds[category] = threshold

    def get_threshold(self, category):
        if category not in self.thresholds:
            return 1.0
        return self.thresholds[category]

    def classify(self, item, default=None):
        probs = {}

        # Find category with highest probs
        max_prob = 0.0
        for category in self.categories():
            probs[category] = self.probability(item, category)
            if probs[category] > max_prob:
                max_prob = probs[category]
                best_category = category

        # Make sure probability > threshold * next best
        for category in probs:
            if category == best_category:
                continue

            if probs[category] * self.get_threshold(best_category) > probs[best_category]:
                return default

        return best_category
