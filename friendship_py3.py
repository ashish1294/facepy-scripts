try :
    from facepy import GraphAPI
    from facepy.exceptions import OAuthError
    import time
    from sys import stdout
except ImportError:
    print("Import Error")

token = 'Enter-Token-Here'
OWNER_NAME = ''
photos_together = {}
no_of_comments = {}
words_in_comment = {}
no_of_messages = {}
total_chat_length = {}

def process_photo_tags(tags):
  #Until we get an empty result page
  if 'error' in tags:
    print("Error = ", error)
    raise Exception("Error in Response")

  if 'data' not in tags:
    return

  while len(tags['data']) > 0:
    #Iterating through all the tags in the current result page
    for tagged_person in tags['data']:
      name = tagged_person['name'].encode('utf-8')
      if name == OWNER_NAME:
        continue
      if name in photos_together:
        #If the tag was encountered before increment
        photos_together[name] += 1
      else:
        #Else initialize new count
        photos_together[name] = 1
    #Get the nect result page
    if 'paging' in tags and 'next' in tags['paging']:
      request_str = tags['paging']['next'].replace('https://graph.facebook.com/', '')
      request_str = request_str.replace('limit=25', 'limit=200')
      tags = graph.get(request_str)
    else:
      tags['data'] = []

def process_photo_comments(comments):

  if 'error' in comments:
    print("Error = ", error)
    raise Exception("Error in Response")

  if 'data' not in comments:
    return

  while len(comments['data']) > 0:
    for comment in comments['data']:
      try:
        commentor = comment['from']['name'].encode('utf-8')
        if commentor == OWNER_NAME:
          #Ignore Comment by owner on his own photos
          continue
        word_count = len(comment['message'].encode('utf-8').split())
      except UnicodeEncodeError:
        print(comment['message'])
        raise Exception('Unicode Encoding Error Encountered')
      if commentor in no_of_comments:
        #If a comment by this person was encountered before
        no_of_comments[commentor] += 1
        words_in_comment[commentor] += word_count
      else:
        #If this is a new commentor
        no_of_comments[commentor] = 1
        words_in_comment[commentor] = word_count
    if 'paging' in comments and 'next' in comments['paging']:
      request_str = comments['paging']['next'].replace('https://graph.facebook.com/', '')
      request_str = request_str.replace('limit=25', 'limit=200')
      comments = graph.get(request_str)
    else:
      comments['data'] = []

def process_photos(photos):
  if 'error' in photos:
    print("Error = ", error)
    raise Exception("Error in Response")

  no_of_photos = 0
  if 'data' not in photos:
    return
  while len(photos['data']) > 0:
    for photo in photos['data']:
      if 'tags' in photo:
        process_photo_tags(photo['tags'])
      if 'comments' in photo:
        process_photo_comments(photo['comments'])
      no_of_photos += 1
      stdout.write("\rNumber of Photos Processed = %d" % no_of_photos)
      stdout.flush()
    if 'paging' in photos and 'next' in photos['paging']:
      request_str = photos['paging']['next'].replace('https://graph.facebook.com/', '')
      request_str = request_str.replace('limit=25', 'limit=200')
      photos = graph.get(request_str)
    else:
      photos['data'] = []

def process_texts(texts, friend_name):
  if 'error' in texts:
    print("Error = ", error)
    raise Exception("Error in Response")

  if 'data' not in texts:
    return
  while len(texts['data']) > 0:
    for text in texts['data']:
      if 'message' not in text:
        #This can happen in message with only an attachment and No text
        continue
      if friend_name in no_of_messages:
        no_of_messages[friend_name] += 1
        total_chat_length[friend_name] += len(text['message'])
      else:
        no_of_messages[friend_name] = 1
        total_chat_length[friend_name] = len(text['message'])
    if 'paging' in texts and 'next' in texts['paging']:
      request_str = texts['paging']['next'].replace('https://graph.facebook.com/', '')
      request_str = request_str.replace('limit=25', 'limit=100')
      success = False
      while not success:
        try:
          texts = graph.get(request_str)
          success = True
        except OAuthError:
          stdout.write("\nCall Limit Exceeded ! Sleeping for 4 min before retrying !!\n")
          for i in range(250):
            stdout.write("\rSleeing.......%d" % i)
            stdout.flush()
            time.sleep(1)
          stdout.write("Woke Up! Retrying !!\n")
    else:
      texts['data'] = []

def process_all_messages(messages):
  if 'error' in messages:
    print("Error = ", error)
    raise Exception("Error in Response")

  if 'data' not in messages:
    return
  while len(messages['data']) > 0:
    for chat in messages['data']:
      if len(chat['to']['data']) != 2:
        #Ignore Group and self messages
        continue
      friend_name = chat['to']['data'][1]['name'].encode('utf-8')
      if friend_name == OWNER_NAME:
        friend_name = chat['to']['data'][0]['name'].encode('utf-8')
      success = False

      while not success:
        try:
          stdout.write("\rProcessing Chat With : %s                     " % friend_name)
          stdout.flush()
          process_texts(chat['comments'], friend_name)
          success = True
        except OAuthError:
          stdout.write("\nCall Limit Exceeded ! Sleeping for 10 min before retrying !!")
          stdout.flush()
          no_of_messages[friend_name] = 0
          total_chat_length[friend_name] = 0
          stdout.write('\n')
          for i in range(600):
            stdout.write("\rSleeing.......%d" % i)
            stdout.flush()
            time.sleep(1)
          stdout.write("Woke Up! Retrying !!")

    if 'paging' in messages and 'next' in messages['paging']:
      request_str = messages['paging']['next'].replace('https://graph.facebook.com/', '')
      request_str = request_str.replace('limit=25', 'limit=400')
      messages = graph.get(request_str)
    else:
      mesages['data'] = []

graph = GraphAPI(token)
me = graph.get('v2.0/me?fields=id,name')
OWNER_NAME = me['name'].encode('utf-8')
photos = graph.get('v2.0/me/photos?fields=comments{message,from},tags{name}&limit=100')
process_photos(photos)
stdout.write('\n\n')
stdout.flush()
inbox = graph.get('v2.0/me/inbox?fields=comments{message},to&limit=100')
process_all_messages(inbox)

top_photos = []
for people in photos_together:
  temp = []
  temp.append(people)
  temp.append(photos_together[people])
  top_photos.append(temp)
top_photos.sort(key=lambda x: x[1], reverse=True)
print("Top People Whom You share photos")
for i in range(5):
  print(i+1, ". ", top_photos[i][0], " - ", top_photos[i][1])

top_commentors = []
for people in no_of_comments:
  temp = []
  temp.append(people)
  temp.append(no_of_comments[people])
  top_commentors.append(temp)
top_commentors.sort(key=lambda x: x[1], reverse=True)
print("Top People Who comments on your photo")
for i in range(5):
  print(i+1, ". ", top_commentors[i][0], " - ", top_commentors[i][1])

long_commentors = []
for people in words_in_comment:
  temp = []
  temp.append(people)
  temp.append(words_in_comment[people])
  long_commentors.append(temp)
long_commentors.sort(key=lambda x: x[1], reverse=True)
print("Top People with most content in comments")
for i in range(5):
  print(i+1, ". ", long_commentors[i][0], " - ", long_commentors[i][1])

top_chatboxes = []
for people in no_of_messages:
  temp = []
  temp.append(people)
  temp.append(no_of_messages[people])
  top_chatboxes.append(temp)
top_chatboxes.sort(key=lambda x:x[1], reverse=True)
print("Top people with most number of Messages")
for i in range(5):
  print(i+1, ". ", top_chatboxes[i][0], " - ", top_chatboxes[i][1])

long_chats = []
for people in total_chat_length:
  temp = []
  temp.append(people)
  temp.append(total_chat_length[people])
  long_chats.append(temp)
long_chats.sort(key=lambda x: x[1], reverse=True)
print("Top People with most content in inbox")
for i in range(5):
  print(i+1, ". ", long_chats[i][0], " - ", long_chats[i][1])

total_count_of_comments = 0
for num in top_commentors:
    total_count_of_comments += num[1]
print("Total Number of comments across all pics = ", total_count_of_comments)
