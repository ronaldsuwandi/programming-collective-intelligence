import feedparser
import re


def read(feed, classifier):
    parsed_feed = feedparser.parse(feed)
    for entry in parsed_feed['entries']:
        print
        print "------"
        print 'Title:     ' + entry['title'].encode('utf-8')
        print 'Publisher: ' + entry['publisher'].encode('utf-8')
        print
        print entry['summary'].encode('utf-8')

        # Combine all the text to create one item for the classifier
        full_text = '%s\n%s\n%s' % (entry['title'], entry['publisher'], entry['summary'])

        # Best guess
        print 'Best guess: ' + str(classifier.classify(full_text))

        # Ask user to specify correct category
        cl = raw_input('Enter category: ')
        classifier.train(full_text, cl)

def entry_features(entry):
    splitter = re.compile('\\W*')
    feature = {}

    # Extract title words
    title_words = [s.lower() for s in splitter.split(entry['title'])
                   if len(s) > 2 and len(s) < 20]
    for word in title_words:
        feature['Title:'+word]=1

    # Extract summary words
    summary_words = [s.lower() for s in splitter.split(entry['summary'])
                     if len(s) > 2 and len(s) <20]

    uppercase_count = 0
    for i in range(len(summary_words)):
        word = summary_words[i]
        feature[word] = 1
        if word.isupper():
            uppercase_count += 1

        # Get word pairs in summary as features
        if i < len(summary_words) - 1:
            two_words = ' '.join(summary_words[i:i+1])
            feature[two_words]=1

    # Keep creator and publisher whole
    feature['Publisher:'+entry['publisher']] = 1

    # UPPERCASE is a virtual word flagging too much shouting
    if float(uppercase_count) / len(summary_words) > 0.3:
        feature['UPPERCASE'] = 1

    return feature
