import json
import os
import unicodecsv as csv
import requests

from bs4 import BeautifulSoup

class Main:
    board_selector = ""
    filename = ""
    
    def boards():
   
        board_list_url = "https://a.4cdn.org/boards.json"
        board_list_response = requests.get(board_list_url)
        board_list_json = json.loads(board_list_response.content)

        boards = []
        board_n = 0
        
        for x in range(len(board_list_json['boards'])):
            board_name = board_list_json['boards'][board_n]['board']
            boards.append(board_name)
            board_description = board_list_json['boards'][board_n]['title']
            if board_list_json['boards'][board_n]['ws_board'] == 0:
                print(f"{board_name} - {board_description} (NSFW)")
            else:
                print(f"{board_name} - {board_description}")
            board_n += 1
        while True:
            board_selector = input("\nPlease select a board\n>")
            if board_selector.lower() in boards and len(board_selector) > 0:
                Main.board_selector += board_selector
                break
            else:
                continue

        url = f"https://a.4cdn.org/{Main.board_selector}/catalog.json"
        return(Main.thread_collector(url))
        
    def thread_collector(url):
        response = requests.get(url)
        board_catalog = json.loads(response.content)

        thread_list = {}

        page_counter = 0 # currently scraping threads from page x
        thread_counter = 0 # scraping thread #y on page x
        for x in range(len(board_catalog)):
            for thread in range(len(board_catalog[page_counter]['threads'])): # threads available on page x (page_counter)
                try: # catches threads with thread names ('sub')
                    thread_name = board_catalog[page_counter]['threads'][thread_counter]['sub']
                    thread_reply_count = board_catalog[page_counter]['threads'][thread_counter]['replies']
                    soup = BeautifulSoup(thread_name, features="html.parser")
                    thread_name_cleaned = soup.get_text()
                    thread_number = board_catalog[page_counter]['threads'][thread_counter]['no']

                    if thread_name_cleaned not in thread_list:
                        thread_list[str(thread_name_cleaned) + " --- " + str(thread_reply_count) + " replies."] = thread_number
                
                except KeyError: # gets triggered when thread doesn't have a thread name
                    thread_name = board_catalog[page_counter]['threads'][thread_counter]['com']
                    thread_reply_count = board_catalog[page_counter]['threads'][thread_counter]['replies']
                    soup = BeautifulSoup(thread_name, features="html.parser")
                    thread_name_cleaned = soup.get_text()
                    thread_number = board_catalog[page_counter]['threads'][thread_counter]['no']                    
                
                    if thread_name_cleaned not in thread_list:
                        thread_list[str(thread_name_cleaned) + " - " + str(thread_reply_count) + " replies."] = thread_number
                
                thread_counter += 1
            
            page_counter += 1 # goes to the next page and resets the...
            thread_counter = 0 # ... thread counter
        return(Main.search_thread(thread_list))

    def search_thread(thread_list):
        search_results = {} # raw list of threads and their thread numbers 
        numbered_results = [] # numbered list of thread names only
        
        print(f"\nCurrently in /{Main.board_selector}/ - type 'return' to return to the main menu\n")
        while True:
            search_query = input("Search for a thread:\n(Leave empty to list all threads)\n>").lower() 
            if search_query == "return":
                Main.board_selector = ""
                return(Main.boards())

            for thread_name, thread_number in thread_list.items():        
                if search_query in thread_name.lower():
                    # if search query is found in thread_list, adds those threads to the search result
                    search_results[thread_name] = thread_number
                
                # adds a number to the left of the thread name 
            for i in range(len(search_results)):
                numbered_results.append((i+1, list(search_results)[i]))
            
            if len(search_results) == 0:
                print("No results, please try again.\n")

            else:
                break
        
        print(f"\nSearch results:\n")
        
        while True:
            try:
                for thread_and_num in numbered_results:
                    print(f"{thread_and_num[0]} {thread_and_num[1]}\n")
                    
                select_thread = input("\nPlease select a thread:\nType 'return' to return to the main menu\nType 'back' to cancel search and return to the current board\n>")
                if select_thread == "return":
                    Main.board_selector = ""
                    return(Main.boards())
                
                if select_thread == "back":
                    return(Main.search_thread(thread_list))
              
                selected_thread_no = thread_list[numbered_results[int(select_thread) - 1][1]]
                selected_thread_name = numbered_results[int(select_thread) - 1][1]
                filename = selected_thread_name.replace(" ","_").replace("/", "|")[:-13] # strips the "- x replies" part of the filename
                Main.filename += filename

                return(Main.csv_writer(selected_thread_name, selected_thread_no, thread_list))
            except ValueError:
                continue

    def csv_writer(thread_name, num, thread_list):
        url = f"https://boards.4channel.org/{Main.board_selector}/thread/{num}.json"
        response = requests.get(url)
        thread = json.loads(response.content)

        post_number = 0
        list_of_ids = []
        new_posts = []

        browse_in_terminal = input("\nWould you like to browse in the terminal or write to a spreadsheet?\n\n1. Browse in terminal\n2. Write to spreadsheet\n>")
        csv_file = f"./threads/{Main.board_selector}/{Main.filename[:100]}/{Main.filename[:100]}.csv"
        csv_folder = f"./threads/{Main.board_selector}/{Main.filename[:100]}"

        os.makedirs(os.path.dirname(csv_file), exist_ok=True)

        # checks if file exists, if so opens in read to append post IDs for later use (checking for new posts)
        try:
            with open(csv_file, mode='rb+') as file:
                reader = csv.reader(file)
                for row in reader: 
                    list_of_ids.append(row[3])

        except FileNotFoundError:
            pass

        for post in thread['posts']:
            timestamp = thread['posts'][post_number]['now']
            try:
                name = thread['posts'][post_number]['name']
            except KeyError:
                name = thread['posts'][post_number]['trip']
            try:
                poster_id = thread['posts'][post_number]['id']
            except:
                poster_id = "No ID"
            
            post_num = str(thread['posts'][post_number]['no'])

            # checks if post has image
            if 'tim' in thread['posts'][post_number]:
                if browse_in_terminal == str(2):
                    linkstring = '=HYPERLINK("'
                    img_name = str(thread['posts'][post_number]['tim']) + 's' + '.jpg'
                    img_url = f"https://i.4cdn.org/{Main.board_selector}/{img_name}"
                     
                    response = requests.get(img_url)
                    if response.status_code == 200:
                        with open(f'{csv_folder}/{img_name}', 'wb') as f:
                            f.write(response.content)
                if browse_in_terminal == str(1):
                    img_name = ""
                    linkstring = ""
            
            if 'com' in thread['posts'][post_number]:
                comment_text = "  " + thread['posts'][post_number]['com']
                try:
                    clean_comment = BeautifulSoup(comment_text, features="html.parser")
                    for br in clean_comment('br'):
                        br.replace_with('\n')
                    clean_comment = clean_comment.text

                except UnboundLocalError:
                    pass

            else:
                clean_comment = "[image]"

            if post_num not in list_of_ids:
                try:
                    if 'tim' in thread['posts'][post_number]:
                        new_posts.append(['\n\n\n', name, poster_id, post_num, f'{linkstring}{img_name}", "[Image Link]")', timestamp, f'\n{clean_comment}'])
                    else:
                        new_posts.append(['\n\n\n', name, poster_id, post_num, '[No Image]', timestamp, f'\n{clean_comment}'])

                except UnboundLocalError:
                    pass            
            post_number += 1  

        if browse_in_terminal == '2':
            print(f"\nDone. \n({len(new_posts)} new posts)")
        
        if browse_in_terminal == '1':
            # checks if file exists - if so it just reads the file
            if os.path.isfile(csv_file):
                os.system(f'column -s -t < "{csv_file}" | less -#3 -N -S')

            # creates a temporary file and deletes it after viewing
            else:                 
                with open(f'./tmp/{Main.filename[:100]}.csv', mode='ab+') as file: 
                    thread_writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
                    for post in new_posts:
                        thread_writer.writerow(post)
                os.system(f'column -s -t < "./tmp/{Main.filename[:100]}.csv" | less -#3 -N -S') & os.system(f'rm "./tmp/{Main.filename[:100]}.csv"')
                os.system(f'rm -r "{csv_folder}"')

        else:
            with open(f'./threads/{Main.board_selector}/{Main.filename[:100]}/{Main.filename[:100]}.csv', mode='ab+') as file:
                    thread_writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
                    for post in new_posts:
                        thread_writer.writerow(post)

        
        Main.filename = ""
        post_number = 0
        list_of_ids = []
        new_posts = []
        num = ""
        return(Main.search_thread(thread_list))
    
Main.boards()

