from tkinter import *
from tkinter import ttk
from utils import *
import search as se



def search(client, query, result):
    try:
        query_terms=query.get()
        search_res = se.search(client, query_terms, 2)

        result.delete(1.0, END)
        for line in search_res["hits"]["hits"]:
            result.insert(END, line)
    except ValueError:
        pass


def main(client):
    root = Tk()
    root.title('Podcast Searcher 3000')

    mainframe = ttk.Frame(root, padding='30 30 30 180')
    mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    #Query bar
    query = StringVar()
    query_entry = ttk.Entry(mainframe, width=60, textvariable=query)
    query_entry.grid(column=1, row=1, sticky=(W, E))

    #Output text
    result = Text(mainframe, width=60, height=40)
    result.grid(row=1, column=2, columnspan=2, rowspan=2, sticky=(N, W, E, S))

    #Search button
    ttk.Button(mainframe, text='Search', command=lambda: search(client, query, result)).grid(column=1, row=2, sticky=W)

    root.bind("<Return>", search)

    root.mainloop()


if __name__ == "__main__":
    client = connect_elastic()
    main(client)
