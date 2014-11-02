import random
import re
import sys
import twitter
import markov
from htmlentitydefs import name2codepoint as n2c
from local_settings import *

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
                     
def grab_tweets(api, user, max_id=None):
    source_tweets=[]
    user_tweets = api.GetUserTimeline(screen_name=user, count=200, max_id=max_id, include_rts=True, trim_user=True, exclude_replies=True)
    returned_tweet_count = len(user_tweets)
    
    if returned_tweet_count-1 < 0: #Seems to fix issue #6. Still not sure WHY this happens; API sometimes returns nothing.
        return source_tweets, 0

    max_id = user_tweets[returned_tweet_count-1].id-1

    for tweet in user_tweets:
        text = filter_tweet(tweet.text)
        if len(text) != 0:
            source_tweets.append(text)

    return source_tweets, max_id

def try_build_tweet(source_tweets):
    mine = markov.MarkovChainer(order)
    
    #get a little crazy (add wodehouse's my man jeeves text)
    mmj = open('jeeves.txt')
    mmj.seek(0)
    data = mmj.read()
    words = data.split()
    for word in words:
        mine.add_text(word)
    mmj.close()
    
    for tweet in source_tweets:
        if re.search('([\.\!\?\"\']$)', tweet):
            pass
        else:
            tweet+="."
        mine.add_text(tweet)
    
    ebook_tweet = mine.generate_sentence()

    #randomly drop the last word, as Horse_ebooks appears to do.
    if random.randint(0,4) == 0 and re.search(r'(in|to|from|for|with|by|our|of|your|around|under|beyond)\s\w+$', ebook_tweet) != None: 
       print "Losing last word randomly"
       ebook_tweet = re.sub(r'\s\w+.$','',ebook_tweet) 
       print ebook_tweet

    #if a tweet is very short, this will randomly add a second sentence to it.
    if ebook_tweet != None and len(ebook_tweet) < 40:
        rando = random.randint(0,10)
        if rando == 0 or rando == 7: 
            print "Short tweet. Adding another sentence randomly"
            newer_tweet = mine.generate_sentence()
            if newer_tweet != None:
                ebook_tweet += " " + mine.generate_sentence()
            else:
                ebook_tweet = ebook_tweet
        elif rando == 1:
            #say something crazy/prophetic in all caps
            print "ALL THE THINGS"
            ebook_tweet = ebook_tweet.upper()

    #throw out tweets that match anything from the source account.
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
    
def get_source_tweets(api):
    source_tweets = []
    
    if STATIC_TEST==True:
        file = TEST_SOURCE
        print ">>> Generating from {0}".format(file)
        string_list = open(file).readlines()
        for item in string_list:
            temp_tweets = item.split(",")
        for tweet in temp_tweets:
            text = filter_tweet(tweet)
            if len(text) != 0:
                source_tweets.append(text)
    else:
        for handle in SOURCE_ACCOUNTS:
            user=handle
            max_id=None
            for x in range(17)[1:]:
                source_tweets_iter, max_id = grab_tweets(api,user,max_id)
                source_tweets += source_tweets_iter   
            print "{0} tweets found in {1}".format(len(source_tweets), handle)
    return source_tweets
	
def post_tweet(api, ebook_tweet):
    if DEBUG == False:
        status = api.PostUpdate(ebook_tweet)
        print status.text.encode('utf-8')
    else:
        print ebook_tweet
	
if __name__=="__main__":
    order = ORDER
    if DEBUG==False:
        guess = random.choice(range(ODDS))
    else:
        guess = 0

    if guess > 0:
        print str(guess) + " No, sorry, not this time." #message if the random number fails.
        sys.exit()
    
    if DEBUG == False or STATIC_TEST == False:
        api = connect()
    else:
        api = None
        
    source_tweets = get_source_tweets(api)
            
    if len(source_tweets) == 0:
        print "Error fetching tweets from Twitter. Aborting."
        sys.exit()
    else:        
        print "{0} total tweets found".format(len(source_tweets))
        
    for x in range(10):	#Try to build a good tweet from the source_tweets. If at first you don't succeed...
        ebook_tweet = try_build_tweet(source_tweets)
        if ebook_tweet != None:
            print "Got a good tweet on iteration "+str(x)+": "+ebook_tweet
            post_tweet(api, ebook_tweet)
            break