import feedparser
    

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
