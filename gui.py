import numpy as np
import traceback
from tkinter import *
from tkinter import ttk
from utils import *
import search as se
import search_show_episode as sse



class SearchRes():
    def __init__(self):
        self.results = dict()
        self.expanded = None
        self.relevance_matrix = None
        self.nDCG_vector = None

    def __len__(self):
        return len(self.results)

    def __getitem__(self, key):
        return self.results[key]
    
    def __setitem__(self, key, value):
        self.results[key] = value

    def set_expand_status(self, key, status):
        self.results[key][2] = status

    def init_vector(self, n, levels):
        self.relevance_matrix = np.zeros((n, levels), dtype=int)
        self.nDCG_vector = np.zeros(n)

    def get_vector(self):
        return self.relevance_matrix.shape[0]

    def get_relevance(self, idx):
        rel = self.relevance_matrix[idx].nonzero()
        if len(rel[0]) > 0:
            return rel[0][0]
        return None

    def set_relevance(self, idx, r):
        self.relevance_matrix[idx] = 0
        self.relevance_matrix[idx, r] = 1

    def vectorize_relevance(self):
        return self.relevance_matrix.nonzero()[1]

    def get_nDCG(self, idx):
        return self.nDCG_vector[idx]
    
    def set_nDCG(self, idx, ndcg):
        self.nDCG_vector[idx] = ndcg

    def clear(self):
        self.results.clear()
        self.relevance_matrix = None
        self.nDCG_vector = None


class SearchGui():
    def __init__(self, root, title):
        self.root = root
        self.root.title(title)
        self.root.option_add('*tearOff', FALSE)
        self.theme = ttk.Style()
        self.theme.theme_use('clam')

        self.text_store = SearchRes()

        #Menu
        self.menubar = Menu(self.root)
        self.root['menu'] = self.menubar
        self.menu_options = Menu(self.menubar)
        self.menubar.add_cascade(menu=self.menu_options, label='Options')
        self.menu_eval = Menu(self.menu_options)
        self.menu_options.add_cascade(menu=self.menu_eval, label='Evaluation')
        self.option = StringVar(None, '0')
        self.menu_eval.add_radiobutton(
            label='None', variable=self.option, value=0, \
            command=lambda v=self.option: self.display_eval(v))
        self.menu_eval.add_radiobutton(
            label='Topical search', variable=self.option, value=1, \
            command=lambda v=self.option: self.display_eval(v))
        self.menu_eval.add_radiobutton(
            label='Refinding or Known item search', variable=self.option, value=2, \
            command=lambda v=self.option: self.display_eval(v))

        #Top frame
        self.mainframe = ttk.Frame(root, padding=20)
        self.mainframe.grid(column=0, row=0, sticky=(N, W, E, S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.mainframe.columnconfigure((0, 1), weight=1)
        self.mainframe.rowconfigure(8, weight=1)

        #Search area frame
        self.topframe = ttk.Frame(self.mainframe, relief='ridge', padding=10)
        self.topframe.grid(column=0, row=0, sticky=(W, E), pady=(0, 20))

        #Query bar
        self.label_q = ttk.Label(self.topframe, text='Enter query:')
        self.label_q.grid(column=0, row=0, sticky=W)
        self.query = StringVar()
        self.query_entry = ttk.Entry(self.topframe, width=80, textvariable=self.query)
        self.query_entry.grid(column=0, row=1, columnspan=3, sticky=(W, E), pady=10)

        #Validation
        def check_choose_n(val):
            return (val.isnumeric() and len(val) < 3 and int(val) >= 0 and int(val) <= 20) or len(val) == 0
        self.check_choose_n_wrapper = (root.register(check_choose_n), '%P')

        #Choose clip size spinbox and label
        self.label_n = ttk.Label(self.topframe, text='Choose clip size (0=automatic, x=30x seconds):')
        self.label_n.grid(column=0, row=3, columnspan=2, sticky=W)
        self.value_n = StringVar()
        self.choose_n = ttk.Spinbox(
            self.topframe, width=7, from_=0, to=20, textvariable=self.value_n, validate='all', \
            validatecommand=self.check_choose_n_wrapper)
        self.choose_n.grid(column=0, row=4, sticky=W, pady=5)
        self.choose_n.config(state=NORMAL)

        #Query type (placed above previous)
        self.querytypes = ['Clips', 'Episodes', 'Shows']
        def disable_clips():
            self.choose_n.config(state=DISABLED)  
        def enable_clips():
            self.choose_n.config(state=NORMAL)
        self.querystates = [enable_clips, disable_clips, disable_clips]

        self.qtype = StringVar(None, 'Clips')
        for i, type in enumerate(self.querytypes):
            self.button = ttk.Radiobutton(self.topframe, text=type, variable=self.qtype, value=type, command=self.querystates[i])
            self.button.grid(column=i, row=2, sticky=W)

        #Choose number of results and label
        self.label_r = ttk.Label(self.topframe, text='Choose maximum number of results (max 200):')
        self.label_r.grid(column=0, row=5, columnspan=2, sticky=W)
        self.value_r = StringVar(None, '20')
        self.num_results_box = ttk.Combobox(
                self.topframe, width=5, state='readonly', textvariable=self.value_r, \
                values=['1', '5', '10', '20', '50', '100', '200'])
        self.num_results_box.grid(column=0, row=6, sticky=W, pady=5)

        #Search button
        self.searchb = ttk.Button(self.topframe, text='Search', \
            command=lambda: self.top_search(
                client, int(self.value_n.get()) if len(self.value_n.get()) > 0 else 0))
        self.searchb.grid(column=0, row=7, sticky=W)

        #Output text
        self.result = Text(self.mainframe, width=80, height=20, state=DISABLED)
        self.text_scroll = ttk.Scrollbar(self.mainframe, orient='vertical', command=self.result.yview)
        self.result['yscrollcommand'] = self.text_scroll.set
        self.result.grid(column=0, row=8, sticky=(N, W, E, S))
        self.text_scroll.grid(column=1, row=8, sticky=(N, S))

        self.root.bind('<Return>',
            lambda event: self.top_search(
                client, int(self.value_n.get()) if len(self.value_n.get()) > 0 else 0))
    

    def display_eval(self, val):
        if val.get() in ['1', '2']:
            #Evaluation area frame
            self.bottomframe = ttk.Frame(self.mainframe, relief='ridge', padding=10)
            self.bottomframe.grid(column=0, row=9, sticky=(W, E), pady=(20, 0))

            #Precision output window and label
            self.label_prec = ttk.Label(self.bottomframe, text='Average precision:')
            self.label_prec.grid(column=0, row=10, pady=(0, 5))
            self.prec_window = Text(self.bottomframe, width=20, height=1, state=DISABLED)
            self.prec_window.grid(column=1, row=10, columnspan=3, sticky=W, padx=15, pady=(0, 5))

            #nDCG output window
            self.compute_window = Text(self.bottomframe, width=20, height=1, state=DISABLED)
            self.compute_window.grid(column=3, row=11, padx=10)

            #nDCG checkbox and label
            self.label_at = ttk.Label(self.bottomframe, text='@')
            self.label_at.grid(column=1, row=11)
            self.nDCG_at = StringVar()
            self.nDCG_box = ttk.Combobox(
                self.bottomframe, width=5, state='readonly', textvariable=self.nDCG_at, values=[str(i) for i in range(1, 21)])
            self.nDCG_box.grid(column=2, row=11, sticky=W)

            #nDCG button
            self.compute = ttk.Button(
                self.bottomframe, text='Compute nDCG', state=DISABLED, \
                    command=lambda: self.nDCG(int(self.nDCG_at.get()) - 1 if len(self.nDCG_at.get()) > 0 else 0))
            self.compute.grid(column=0, row=11)
        else:
            if hasattr(self, 'bottomframe'):
                self.bottomframe.grid_remove()
        
    
    def top_search(self, client, value_n):
        self.search_type = self.qtype.get()
        if self.search_type == 'Clips':
            self.search_clips(client, value_n)
        elif self.search_type == 'Episodes':
            self.search_episodes(client)
        else:
            pass

    
    def text_search(self, text, word, window):
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
    

    def text_delete(self, event, text, idx, type='clip'):
        self.text_store.set_expand_status(idx, False)
        next_line = int(text[0].split('.')[0]) + 1
        if type == 'clip':
            event.widget.delete(text[0],  str(next_line) + '.0')
        elif type == 'episode':
            start = text[0]
            for i in range(len(text[1])):
                event.widget.delete(start, str(next_line) + '.0')
        self.text_store.expanded = None
    

    ######################
    #
    #TAG-RELATED FUNCTIONS
    #
    ######################

    def ep_test(self, event, tag):
        print(tag, event.widget.get(f'{tag}.first', f'{tag}.last'))


    def text_expand(self, event, tag, type='clip'):
        idx = int(tag.split('_')[1])
        text = self.text_store[idx]
        event.widget.config(state=NORMAL)
        if self.text_store.expanded is not None and self.text_store.expanded != idx:
            self.text_delete(
                event, self.text_store[self.text_store.expanded], self.text_store.expanded, \
                'clip' if type == 'clip' else 'episode')
        if not text[2]:
            self.text_store.set_expand_status(idx, True)
            if type == 'clip':
                event.widget.insert(text[0], text[1] + '\n')
            elif type == 'episode':
                start = text[0]
                for clip in text[1]:
                    event.widget.insert(start, clip + '\n')
                    start = str(int(start.split('.')[0]) + 1) + '.0'
            self.text_store.expanded = idx
        else:
            self.text_delete(event, text, idx, 'clip' if type == 'clip' else 'episode')
        event.widget.config(state=DISABLED)
        return 'break'


    def relevance(self, event, tag):
        idx = int(tag.split('_')[1])
        r = int(event.widget.get(f'{tag}.first', f'{tag}.last').strip())
        if self.text_store.get_relevance(idx) is not None:
            other_r = 0
            for i, span in enumerate(event.widget.tag_ranges('boldtext')):
                if span.string.split('.')[0] == event.widget.index(f'{tag}.first').split('.')[0]:
                    other_r = i
                    break
            event.widget.tag_remove(
                'boldtext', event.widget.tag_ranges('boldtext')[other_r], \
                event.widget.tag_ranges('boldtext')[other_r+1])
        self.text_store.set_relevance(idx, r)
        event.widget.tag_add('boldtext', f'{tag}.first', f'{tag}.last')
        sum_rel = 0
        prec = []
        for i in range(self.text_store.get_vector()):
            rel = self.text_store.get_relevance(i)
            if rel not in [None, 0]:
                sum_rel += 1
                prec.append(sum_rel / (i+1))
        self.prec_window.config(state=NORMAL)
        self.prec_window.delete(1.0, END)
        self.prec_window.insert(END, round(1/len(prec) * sum(prec), 4) if len(prec) > 0 else 0.0)
        self.prec_window.config(state=DISABLED)

    ######################

    
    def search_clips(self, client, value_n):
        try:
            eval = self.option.get()
            if eval in ['1', '2']:
                self.compute_window.config(state=NORMAL)
                self.prec_window.config(state=NORMAL)
                self.compute_window.delete(1.0, END)
                self.prec_window.delete(1.0, END)
                self.compute_window.config(state=DISABLED)
                self.prec_window.config(state=DISABLED)
                self.compute.config(state=DISABLED)
                self.nDCG_box.config(state=DISABLED)
            self.result.config(state=NORMAL)
            self.result.delete(1.0, END)
            self.text_store.clear()

            query_terms = self.query.get()
            if len(query_terms.rstrip()) == 0:
                self.result.insert(END, 'Please enter a search query in the query bar.')
                self.result.config(state=DISABLED)
                return
            w = query_terms.split()[0].lower()
            search_res = se.search(client, query_terms, value_n, int(self.value_r.get()), 'specified' if value_n > 0 else 'automatic')

            if len(search_res) == 0:
                self.result.insert(END, 'No results found.')
            else:
                self.text_store.init_vector(len(search_res), 4 if self.option in ['0', '1'] else 5)
                for i, line in enumerate(search_res):
                    #Tags
                    self.result.tag_config('boldtext', font=f'{self.result.cget("font")} 12 bold')
                    tag = f'tag_{i}'
                    self.result.tag_config(tag, foreground='blue')
                    self.result.tag_bind(tag, '<Button-1>', lambda e, t=tag: self.ep_test(e, t))
                    tag_expand = f'tagexp_{i}'
                    self.result.tag_config(tag_expand)
                    self.result.tag_bind(
                        tag_expand, '<Button-1>', lambda e, t=tag_expand, s='clip': self.text_expand(e, t, s))
                    if eval in ['1', '2']:
                        tag_rel0 = f'tagrel0_{i}'
                        self.result.tag_config(tag_rel0)
                        self.result.tag_bind(
                            tag_rel0, '<Button-1>', lambda e, t=tag_rel0: self.relevance(e, t))
                        tag_rel1 = f'tagrel1_{i}'
                        self.result.tag_config(tag_rel1)
                        self.result.tag_bind(
                            tag_rel1, '<Button-1>', lambda e, t=tag_rel1: self.relevance(e, t))
                        tag_rel2 = f'tagrel2_{i}'
                        self.result.tag_config(tag_rel2)
                        self.result.tag_bind(
                            tag_rel2, '<Button-1>', lambda e, t=tag_rel2: self.relevance(e, t))
                        tag_rel3 = f'tagrel3_{i}'
                        self.result.tag_config(tag_rel3)
                        self.result.tag_bind(
                            tag_rel3, '<Button-1>', lambda e, t=tag_rel3: self.relevance(e, t))
                        if eval == '2':
                            tag_rel4 = f'tagrel4_{i}'
                            self.result.tag_config(tag_rel4)
                            self.result.tag_bind(
                                tag_rel4, '<Button-1>', lambda e, t=tag_rel4: self.relevance(e, t))
                    #Show title
                    self.result.insert(END, f'{i+1}. {line[2]}\n', (tag_expand,))
                    #Episode title
                    self.result.insert(END, f'{line[3]}\n', (tag, tag_expand))
                    #Text
                    indices = [self.result.index('end')]
                    indices.append(line[4])
                    indices.append(False)
                    self.text_store[i] = indices
                    self.result.insert(END, f'{self.text_search(line[4], w, 6)}\nscore: {line[1]}\n', (tag_expand,))
                    if eval in ['1', '2']:
                        self.result.insert(END, 'Select relevance:')
                        self.result.insert(END, '\t0\t', (tag_rel0,))
                        self.result.tag_add('boldtext', f'{tag_rel0}.first', f'{tag_rel0}.last')
                        self.text_store.set_relevance(i, 0)
                        self.result.insert(END, '\t1', (tag_rel1,))
                        self.result.insert(END, '\t2', (tag_rel2,))
                        self.result.insert(END, '\t3', (tag_rel3,))
                        if eval != '2':
                            self.result.insert(END, '\n')
                        else:
                            self.result.insert(END, '\t4', (tag_rel4,))
                    self.result.insert(END, '\n---------\n')
                if eval in ['1', '2']:
                    self.compute.config(state=NORMAL)
                    self.nDCG_box.config(state=NORMAL)

            self.result.config(state=DISABLED)
        except Exception:
            print(traceback.format_exc())
            self.result.insert(END, 'Error during search.')
            self.result.config(state=DISABLED)
    

    def search_episodes(self, client):
        try:
            eval = self.option.get()
            if eval in ['1', '2']:
                self.compute_window.config(state=NORMAL)
                self.prec_window.config(state=NORMAL)
                self.compute_window.delete(1.0, END)
                self.prec_window.delete(1.0, END)
                self.compute_window.config(state=DISABLED)
                self.prec_window.config(state=DISABLED)
                self.compute.config(state=DISABLED)
                self.nDCG_box.config(state=DISABLED)
            self.result.config(state=NORMAL)
            self.result.delete(1.0, END)
            self.text_store.clear()

            query_terms = self.query.get()
            if len(query_terms.rstrip()) == 0:
                self.result.insert(END, 'Please enter a search query in the query bar.')
                self.result.config(state=DISABLED)
                return
            search_res, num_clips = sse.episode_search(client, query_terms, int(self.value_r.get()))

            if len(search_res) == 0:
                self.result.insert(END, 'No results found.')
            else:
                self.text_store.init_vector(num_clips, 4 if self.option in ['0', '1'] else 5)
                clip_counter = 0
                for i, line in enumerate(search_res):
                    #Tags
                    self.result.tag_config('boldtext', font=f'{self.result.cget("font")} 12 bold')
                    tag = f'tag_{i}'
                    self.result.tag_config(tag, foreground='blue')
                    self.result.tag_bind(tag, '<Button-1>', lambda e, t=tag: self.ep_test(e, t))
                    tag_expand = f'tagexp_{i}'
                    self.result.tag_config(tag_expand)
                    self.result.tag_bind(
                        tag_expand, '<Button-1>', lambda e, t=tag_expand, s='episode': self.text_expand(e, t, s))
                    if eval in ['1', '2']:
                        for j in range(len(line[1]['clips'])):
                            tag_rel0 = f'tagrel0_{clip_counter+j}'
                            self.result.tag_config(tag_rel0)
                            self.result.tag_bind(
                                tag_rel0, '<Button-1>', lambda e, t=tag_rel0: self.relevance(e, t))
                            tag_rel1 = f'tagrel1_{clip_counter+j}'
                            self.result.tag_config(tag_rel1)
                            self.result.tag_bind(
                                tag_rel1, '<Button-1>', lambda e, t=tag_rel1: self.relevance(e, t))
                            tag_rel2 = f'tagrel2_{clip_counter+j}'
                            self.result.tag_config(tag_rel2)
                            self.result.tag_bind(
                                tag_rel2, '<Button-1>', lambda e, t=tag_rel2: self.relevance(e, t))
                            tag_rel3 = f'tagrel3_{clip_counter+j}'
                            self.result.tag_config(tag_rel3)
                            self.result.tag_bind(
                                tag_rel3, '<Button-1>', lambda e, t=tag_rel3: self.relevance(e, t))
                            if eval == '2':
                                tag_rel4 = f'tagrel4_{clip_counter+j}'
                                self.result.tag_config(tag_rel4)
                                self.result.tag_bind(
                                    tag_rel4, '<Button-1>', lambda e, t=tag_rel4: self.relevance(e, t))
                    #Episode title
                    self.result.insert(END, f'{i+1}. {line[0]}\n', (tag, tag_expand))
                    #Show title
                    self.result.insert(END, f'{line[1]["show name"]}\n', (tag_expand,))
                    #Text
                    indices = [self.result.index('end')]
                    clip_str = []
                    for j, clip in enumerate(line[1]['clips']):
                        clip_str.append(f'Clip {clip_counter+1+j}. ' + clip[2])
                    indices.append(clip_str)
                    indices.append(False)
                    self.text_store[i] = indices
                    self.result.insert(END, f'Description: {line[1]["episode description"]}\nscore: {line[1]["score"]}\n', (tag_expand,))
                    if eval in ['1', '2']:
                        for j in range(len(line[1]['clips'])):
                            self.result.insert(END, 'Select relevance:')
                            tag_rel0 = f'tagrel0_{clip_counter+j}'
                            self.result.insert(END, '\t0\t', (tag_rel0,))
                            self.result.tag_add('boldtext', f'{tag_rel0}.first', f'{tag_rel0}.last')
                            self.text_store.set_relevance(clip_counter+j, 0)
                            self.result.insert(END, '\t1', (f'tagrel1_{clip_counter+j}',))
                            self.result.insert(END, '\t2', (f'tagrel2_{clip_counter+j}',))
                            self.result.insert(END, '\t3', (f'tagrel3_{clip_counter+j}',))
                            if eval != '2':
                                self.result.insert(END, '\n')
                            else:
                                self.result.insert(END, '\t4', (f'tagrel4_{clip_counter+j}',))
                                self.result.insert(END, '\n')
                    self.result.insert(END, '---------\n')
                    clip_counter += len(line[1]['clips'])

                if eval in ['1', '2']:
                    self.compute.config(state=NORMAL)
                    self.nDCG_box.config(state=NORMAL)

            self.result.config(state=DISABLED)

        except Exception:
            print(traceback.format_exc())
            self.result.insert(END, 'Error during search.')
            self.result.config(state=DISABLED)
    
    def nDCG(self, rank):
        relevance_vector = self.text_store.vectorize_relevance()
        sorted_vector = np.sort(relevance_vector)[::-1]
        num_results = len(relevance_vector)
        dCG, iDCG = 0, 0
        for i in range(num_results):
            dCG += relevance_vector[i] / np.log2(i+2)
            iDCG += sorted_vector[i] / np.log2(i+2)
            self.text_store.set_nDCG(i, round(dCG / iDCG, 4) if iDCG > 0 else 0)
        self.compute_window.config(state=NORMAL)
        self.compute_window.delete(1.0, END)
        self.compute_window.insert(END, self.text_store.get_nDCG(rank if rank < num_results else num_results-1))
        self.compute_window.config(state=DISABLED)


if __name__ == "__main__":
    client = connect_elastic()
    root = Tk()
    app = SearchGui(root, 'Spotify Podcast Search')
    root.mainloop()
