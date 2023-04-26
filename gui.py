from tkinter import *
from tkinter import ttk
from utils import *
import search as se



def search(client, query, result):
    try:
        query_terms=query.get()
        search_res = se.search(client, query_terms, 2)

        result.config(state=NORMAL)
        result.delete(1.0, END)
        if len(search_res['hits']['hits']) == 0:
            result.insert(END, 'No results found.')
        else:
            for line in search_res["hits"]["hits"]:
                line_str = []
                line_str.append(line['_source']['show_name'] + '\n')
                line_str.append(line['_source']['ep_name'] + '\n')
                line_str.append(line['_source']['words'] + '\n')
                line_str.append('score: ' + str(line['_score']) + '\n')
                line_str.append('---------\n')
                result.insert(END, ''.join(line_str))
        result.config(state=DISABLED)
    except:
        print('Error during search.')
        result.config(state=DISABLED)


def main(client):
    root = Tk()
    root.title('Podcast Searcher 3000')

    mainframe = ttk.Frame(root, padding='30 30 30 30')
    mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    #Query bar
    query = StringVar()
    query_entry = ttk.Entry(mainframe, width=80, textvariable=query)
    query_entry.grid(column=1, row=1, sticky=(W, E))

    #Validation
    def check_choose_n(val):
        return (val.isnumeric() and len(val) < 3 and int(val) > 0 and int(val) <= 20) or len(val) == 0
    check_choose_n_wrapper = (root.register(check_choose_n), '%P')

    #Choose clip size spinbox and label
    label_n = ttk.Label(mainframe, text='Choose clip size (1=30 seconds):') \
        .grid(column=1, row=2, sticky=W)
    value_n = StringVar()
    choose_n = ttk.Spinbox(mainframe, width=7, from_=1, to=20, textvariable=value_n, validate='all', validatecommand=check_choose_n_wrapper)
    choose_n.grid(column=1, row=3, sticky=W)

    #Output text
    result = Text(mainframe, width=80, height=20)
    ys = ttk.Scrollbar(mainframe, orient='vertical', command=result.yview)
    result['yscrollcommand'] = ys.set
    result.grid(row=6, column=1, columnspan=2, rowspan=2, sticky=(N, W, E, S))
    ys.grid(row=6, column=3, rowspan=2, sticky=(N, S))

    #Search button
    ttk.Button(mainframe, text='Search', command=lambda: search(client, query, result)) \
        .grid(column=1, row=4, sticky=W)

    for child in mainframe.winfo_children():
        child.grid_configure(pady=10)

    root.bind('<Return>', lambda event: search(client, query, result))

    root.mainloop()


if __name__ == "__main__":
    client = connect_elastic()
    main(client)
