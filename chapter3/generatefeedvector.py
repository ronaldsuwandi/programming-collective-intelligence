import feedparser
import re


# Returns title and dictionary of word counts for an RSS feed
def get_word_counts(url):
    # Parse feed
    d = feedparser.parse(url)
    wc = {}

    for e in d.entries:
        if 'summary' in e:
            summary = e.summary
        else:
            summary = e.description

        words = get_words(e.title + ' ' + summary)
        for word in words:
            wc.setdefault(word, 0)
            wc[word] += 1

    return d.feed.title, wc


def get_words(html):
    # Remove HTML tags
    txt = re.compile(r'<[^>]+>').sub('', html)

    # Split words by all non-alpha characters
    words = re.compile(r'[^A-Z^a-z]+').split(txt)

    # Convert to lowercase
    return [word.lower() for word in words if word != '']


apcount = {}
wordcounts = {}
feedlist = []
for feedurl in open('/Users/rsuwandi/Personal/programming-collective-intelligence/chapter3/feedlist.txt'):
    feedlist.append(feedurl)
    title, wc = get_word_counts(feedurl)
    wordcounts[title] = wc
    for word, count in wc.items():
        apcount.setdefault(word, 0)
        if count > 1:
            apcount[word] += 1

wordlist = []
for w, bc in apcount.items():
    frac = float(bc) / len(feedlist)
    if frac > 0.1 and frac < 0.5:
        wordlist.append(w)

out = open('/Users/rsuwandi/Personal/programming-collective-intelligence/chapter3/blogdata-generated.txt', 'w')
out.write('Blog')

for word in wordlist:
    out.write('\t%s' % word)

out.write('\n')
for blog, wc in wordcounts.items():
    # Deal with unicode outside ascii range
    blog = blog.encode('ascii', 'ignore')
    out.write(str(blog))
    for word in wordlist:
        if word in wc:
            out.write('\t%d' % wc[word])
        else:
            out.write('\t0')
    out.write('\n')
