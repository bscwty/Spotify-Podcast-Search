import numpy as np
import traceback
from tkinter import *
from tkinter import ttk
from utils import *
import search as se



class SearchRes():
    def __init__(self):
        self.results = dict()
        self.expanded = None
        self.relevance_vector = None

    def __len__(self):
        return len(self.results)

    def __getitem__(self, key):
        return self.results[key]
    
    def __setitem__(self, key, value):
        self.results[key] = value

    def set_expand_status(self, key, status):
        self.results[key][2] = status

    def init_vector(self, n):
        self.relevance_vector = np.zeros((n, 4), dtype=int)

    def get_relevance(self, idx):
        rel = self.relevance_vector[idx].nonzero()
        if len(rel[0]) > 0:
            return rel[0][0]
        return None

    def set_relevance(self, idx, r):
        self.relevance_vector[idx] = 0
        self.relevance_vector[idx, r] = 1

    def clear(self):
        self.results.clear()
        self.relevance_vector = None


def text_search(text, word, window):
    words = text.lower().split()
    idx = None
    for i, w in enumerate(words):
        if word in w:
            idx = i
            break
    if idx is None:
        return ' '.join(words[:min(window*2, len(words))])

    start_ell = '...' if max(idx - window, 0) > 0 else ''
    end_ell = '...' if min(idx + window, len(words)) < len(words) else ''
    return start_ell + ' '.join(words[max(idx - window, 0):min(idx + window, len(words))]) + end_ell


def text_delete(event, clips, text, idx):
    clips.set_expand_status(idx, False)
    next_line = int(text[0].split('.')[0]) + 1
    event.widget.delete(text[0],  str(next_line) + '.0')
    clips.expanded = None


######################
#
#TAG-RELATED FUNCTIONS
#
######################

def ep_test(event, tag):
    print(tag, event.widget.get(f'{tag}.first', f'{tag}.last'))


def text_expand(event, tag, clips):
    idx = int(tag.split('_')[1])
    text = clips[idx]
    event.widget.config(state=NORMAL)
    if clips.expanded is not None and clips.expanded != idx:
        text_delete(event, clips, clips[clips.expanded], clips.expanded)
    if not text[2]:
        clips.set_expand_status(idx, True)
        event.widget.insert(text[0], text[1] + '\n')
        clips.expanded = idx
    else:
        text_delete(event, clips, text, idx)
    event.widget.config(state=DISABLED)
    return 'break'


def relevance(event, tag, clips):
    idx = int(tag.split('_')[1])
    r = int(event.widget.get(f'{tag}.first', f'{tag}.last').strip())
    if clips.get_relevance(idx) is not None:
        other_r = 0
        for i, span in enumerate(event.widget.tag_ranges('boldtext')):
            if span.string.split('.')[0] == event.widget.index(f'{tag}.first').split('.')[0]:
                other_r = i
                break
        event.widget.tag_remove('boldtext', event.widget.tag_ranges('boldtext')[other_r], event.widget.tag_ranges('boldtext')[other_r+1])
    clips.set_relevance(idx, r)
    event.widget.tag_add('boldtext', f'{tag}.first', f'{tag}.last')

######################


def top_search(client, query, value_n, qtype, result, text_store):
    search_type = qtype.get()
    if search_type == 'Clips':
        search_clips(client, query, value_n, result, text_store)
    elif search_type == 'Episodes':
        pass
    else:
        pass


def search_clips(client, query, value_n, result, text_store):
    try:
        result.config(state=NORMAL)
        result.delete(1.0, END)
        text_store.clear()

        query_terms = query.get()
        if len(query_terms.rstrip()) == 0:
            result.insert(END, 'Please enter a search query in the query bar.')
            result.config(state=DISABLED)
            return
        w = query_terms.split()[0].lower()
        search_res = se.search(client, query_terms, value_n, 'specified' if value_n > 0 else 'automatic')

        if len(search_res) == 0:
            result.insert(END, 'No results found.')
        else:
            text_store.init_vector(len(search_res))
            for i, line in enumerate(search_res):
                #Tags
                result.tag_config('boldtext', font=f'{result.cget("font")} 12 bold')
                tag = f'tag_{i}'
                result.tag_config(tag, foreground='blue')
                result.tag_bind(tag, '<Button-1>', lambda e, t=tag: ep_test(e, t))
                tag_expand = f'tagexp_{i}'
                result.tag_config(tag_expand)
                result.tag_bind(tag_expand, '<Button-1>', lambda e, t=tag_expand, clips=text_store: text_expand(e, t, clips))
                tag_rel0 = f'tagrel0_{i}'
                result.tag_config(tag_rel0)
                result.tag_bind(tag_rel0, '<Button-1>', lambda e, t=tag_rel0, clips=text_store: relevance(e, t, clips))
                tag_rel1 = f'tagrel1_{i}'
                result.tag_config(tag_rel1)
                result.tag_bind(tag_rel1, '<Button-1>', lambda e, t=tag_rel1, clips=text_store: relevance(e, t, clips))
                tag_rel2 = f'tagrel2_{i}'
                result.tag_config(tag_rel2)
                result.tag_bind(tag_rel2, '<Button-1>', lambda e, t=tag_rel2, clips=text_store: relevance(e, t, clips))
                tag_rel3 = f'tagrel3_{i}'
                result.tag_config(tag_rel3)
                result.tag_bind(tag_rel3, '<Button-1>', lambda e, t=tag_rel3, clips=text_store: relevance(e, t, clips))
                #Show title
                result.insert(END, f'{i+1}. {line[2]}\n', (tag_expand,))
                #Episode title
                result.insert(END, f'{line[3]}\n', (tag, tag_expand))
                #Text
                indices = [result.index('end')]
                indices.append(line[4])
                indices.append(False)
                text_store[i] = indices
                result.insert(END, f'{text_search(line[4], w, 6)}\nscore: {line[1]}\n', (tag_expand,))
                result.insert(END, 'Select relevance:')
                result.insert(END, '\t0\t', (tag_rel0,))
                result.tag_add('boldtext', f'{tag_rel0}.first', f'{tag_rel0}.last')
                text_store.set_relevance(i, 0)
                result.insert(END, '\t1', (tag_rel1,))
                result.insert(END, '\t2', (tag_rel2,))
                result.insert(END, '\t3\n', (tag_rel3,))
                result.insert(END, '---------\n')

        result.config(state=DISABLED)
    except Exception:
        print(traceback.format_exc())
        result.insert(END, 'Error during search.')
        result.config(state=DISABLED)


def main(client):
    root = Tk()
    root.title('Spotify Podcast Search')
    theme = ttk.Style()
    theme.theme_use('clam')

    mainframe = ttk.Frame(root, padding=20)
    mainframe.grid(column=0, row=0, sticky=(N, W, E, S))

    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    mainframe.columnconfigure((0, 1), weight=1)
    mainframe.rowconfigure(6, weight=1)

    #Search area frame
    topframe = ttk.Frame(mainframe, relief='ridge', padding=10)
    topframe.grid(column=0, row=0, pady=(0, 20))

    #Query bar
    label_q = ttk.Label(topframe, text='Enter query:')
    label_q.grid(column=0, row=0, sticky=W)
    query = StringVar()
    query_entry = ttk.Entry(topframe, width=80, textvariable=query)
    query_entry.grid(column=0, row=1, columnspan=3, sticky=(W, E), pady=10)

    #Validation
    def check_choose_n(val):
        return (val.isnumeric() and len(val) < 3 and int(val) >= 0 and int(val) <= 20) or len(val) == 0
    check_choose_n_wrapper = (root.register(check_choose_n), '%P')

    #Choose clip size spinbox and label
    label_n = ttk.Label(topframe, text='Choose clip size (0=automatic, x=30x seconds):')
    label_n.grid(column=0, row=3, columnspan=2, sticky=W)
    value_n = StringVar()
    choose_n = ttk.Spinbox(topframe, width=7, from_=0, to=20, textvariable=value_n, validate='all', validatecommand=check_choose_n_wrapper)
    choose_n.grid(column=0, row=4, sticky=W)
    choose_n.config(state=NORMAL)

    #Query type (placed above previous)
    querytypes = ['Clips', 'Episodes', 'Shows']
    def disable_clips():
        choose_n.config(state=DISABLED)  
    def enable_clips():
        choose_n.config(state=NORMAL)
    querystates = [enable_clips, disable_clips, disable_clips]

    qtype = StringVar(None, 'Clips')
    for i, type in enumerate(querytypes):
        button = ttk.Radiobutton(topframe, text=type, variable=qtype, value=type, command=querystates[i])
        button.grid(column=i, row=2, sticky=W)

    text_store = SearchRes()

    #Search button
    searchb = ttk.Button(topframe, text='Search', \
            command=lambda: top_search(
                client, query, int(value_n.get()) if len(value_n.get()) > 0 else 0, qtype, result, text_store))
    searchb.grid(column=0, row=5, sticky=W)

    #Output text
    result = Text(mainframe, width=80, height=20)
    text_scroll = ttk.Scrollbar(mainframe, orient='vertical', command=result.yview)
    result['yscrollcommand'] = text_scroll.set
    result.grid(column=0, row=6, sticky=(N, W, E, S))
    text_scroll.grid(column=1, row=6, sticky=(N, S))

    root.bind('<Return>',
              lambda event: top_search(client, query, int(value_n.get()) if len(value_n.get()) > 0 else 0, qtype, result, text_store))

    root.mainloop()


if __name__ == "__main__":
    client = connect_elastic()
    main(client)
