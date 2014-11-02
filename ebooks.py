import getopt
import random
import re
import sys
import twitter
import markov3 as markov
from htmlentitydefs import name2codepoint as n2c
from local_settings import *

# build a (connected) Twitter API object
def connect():
    api = twitter.Api(consumer_key=MY_CONSUMER_KEY,
                          consumer_secret=MY_CONSUMER_SECRET,
                          access_token_key=MY_ACCESS_TOKEN_KEY,
                          access_token_secret=MY_ACCESS_TOKEN_SECRET)
    return api

def entity(text):
    if text[:2] == "&#":
        try:
            if text[:3] == "&#x":
                return unichr(int(text[3:-1], 16))
            else:
                return unichr(int(text[2:-1]))
        except ValueError:
            pass
    else:
        guess = text[1:-1]
        numero = n2c[guess]
        try:
            text = unichr(numero)
        except KeyError:
            pass    
    return text

# filter/clean tweets
def filter_tweet(text):
    text = re.sub(r'\b(RT|MT) .+','',text) #take out anything after RT or MT
    text = re.sub(r'(\#|@|(h\/t)|(http))\S+','',text) #Take out URLs, hashtags, hts, etc.
    text = re.sub(r'\n','', text) #take out new lines.
    text = re.sub(r'\"|\(|\)', '', text) #take out quotes.
    htmlsents = re.findall(r'&\w+;', text)
    if len(htmlsents) > 0 :
        for item in htmlsents:
            text = re.sub(item, entity(item), text)    
    text = re.sub(r'\xe9', 'e', text) #take out accented e
    return text
 
# get filtered tweets from a source account (in chunks)
def grab_tweets(api, user, max_id=None):
    source_tweets=[]
    user_tweets = api.GetUserTimeline(screen_name=user, count=200, max_id=max_id, include_rts=True, trim_user=True, exclude_replies=True)
    returned_tweet_count = len(user_tweets)
    
    # if api returned nothing, return an empty list and max_id of zero to prevent exception
    if returned_tweet_count-1 < 0: 
        return source_tweets, 0

    max_id = user_tweets[returned_tweet_count-1].id-1

    # filter source tweets
    for tweet in user_tweets:
        text = filter_tweet(tweet.text)
        if len(text) != 0:
            source_tweets.append(text)

    return source_tweets, max_id

def markov_file_adder(mine, filename):
    # add additional words from words/ files to 
    # increase vocabulary
    with open(filename, "rt") as f:
        text = f.read()
    
    words = text.split('.')
    for sent in words:
        sent = filter_tweet(sent)
        mine.add_text(sent)
        
    return mine
    
def markov_list_adder(mine, list):
    # ensure punctuation on tweets
    for item in list:
        if re.search('([\.\!\?\"\']$)', item):
            pass
        else:
            item+="."
        mine.add_text(item)
        
    return mine

# try to build a tweet using markov chaining
def try_build_tweet(source_tweets, order):
    
    mine = markov.MarkovChainer(order)
    #mine = markov_file_adder(mine, 'words/jeeves.txt')
    mine = markov_list_adder(mine, source_tweets)
    
    # let markov generate sentence
    ebook_tweet = mine.generate_sentence()

    # randomly drop the last word, as Horse_ebooks appears to do.
    if random.randint(0,4) == 0 and re.search(r'(in|to|from|for|with|by|our|of|your|around|under|beyond)\s\w+$', ebook_tweet) != None: 
       print "Losing last word randomly"
       ebook_tweet = re.sub(r'\s\w+.$','',ebook_tweet) 
       print ebook_tweet

    # if a tweet is very short, this will randomly add a second sentence to it.
    # odds of adding a sentence improve as the tweet gets shorter
    if ebook_tweet != None and len(ebook_tweet) < 40:
        max = (len(ebook_tweet) + 10 // 2) // 10
        rando = random.randint(0,max)
        if rando == 0: 
            print "Short tweet. Adding another sentence randomly"
            newer_tweet = mine.generate_sentence()
            if newer_tweet != None:
                ebook_tweet += " " + mine.generate_sentence()
            else:
                ebook_tweet = ebook_tweet

    # throw out tweets that match anything from the source account.
    if ebook_tweet != None and len(ebook_tweet) < 110:
        for tweet in source_tweets:
            if ebook_tweet[:-1] not in tweet:
                continue
            else: 
                print "TOO SIMILAR: " + ebook_tweet
                ebook_tweet = None
                break;

    elif ebook_tweet == None:
        print "EMPTY TWEET"
    else:
        print "TOO LONG: " + ebook_tweet
        ebook_tweet = None
            
    return ebook_tweet
    
# get source tweets to drive tweet-making
def get_source_tweets(api, static_test):
    source_tweets = []
    # read strings from flat-file
    if static_test == True:
        file = TEST_SOURCE
        print ">>> Generating from {0}".format(file)
        string_list = open(file).readlines()
        for item in string_list:
            temp_tweets = item.split(",")
        for tweet in temp_tweets:
            text = filter_tweet(tweet)
            if len(text) != 0:
                source_tweets.append(text)
    # read tweets from source accounts
    else:
        for handle in SOURCE_ACCOUNTS:
            user=handle
            max_id=None
            for x in range(17)[1:]:
                source_tweets_iter, max_id = grab_tweets(api,user,max_id)
                source_tweets += source_tweets_iter   
            print "{0} tweets found in {1}".format(len(source_tweets), handle)
    return source_tweets

# post tweet to twitter (or console)
def post_tweet(api, debug, ebook_tweet):
    if debug == True:
        print "DEBUG: " + ebook_tweet
    else:
        status = api.PostUpdate(ebook_tweet)
        print status.text.encode('utf-8')        

def main(argv):
    order = ORDER # set tweet sanity
    static_test = STATIC_TEST
    debug = DEBUG
    
    # check args for debug override or static test override
    try:
        opts, args = getopt.getopt(argv,"hds")
    except getopt.GetoptError:
      print 'ebooks.py [-d] [-s]'
      sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'ebooks.py [-d] [-s]'
            sys.exit()
        elif opt in ("-s", "--static"):
            static_test = True
            print 'Running a static test'
        elif opt in ("-d", "--debug"):
            print 'Running in debug mode'
            debug = True
    
    # determine odds of running
    if debug==False:
        guess = random.choice(range(ODDS))
    else:
        guess = 0

    if guess > 0:
        print str(guess) + " No, sorry, not this time."
        sys.exit()

    # connect to API if necessary
    if debug == False or static_test == False:
        api = connect()
    else:
        api = None
        
    # get tweets from the source account / flat file
    source_tweets = get_source_tweets(api, static_test)
    
    # make sure we have tweets to work with
    if len(source_tweets) == 0:
        print "Error fetching tweets from Twitter. Aborting."
        sys.exit()
    else:        
        print "{0} total tweets found".format(len(source_tweets))
        
    # try to build a good tweet from the source_tweets. If at first you don't succeed...
    for x in range(20):	
        ebook_tweet = try_build_tweet(source_tweets, order)
        if ebook_tweet != None:
            print "Iteration: " + str(x)
            post_tweet(api, debug, ebook_tweet)
            break
            
if __name__ == "__main__":
    main(sys.argv[1:])