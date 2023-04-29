from django.shortcuts import render
from django.views import View
from django.conf import settings
from django.http import HttpResponseRedirect
from django.db import connections

from .forms import BlacklistForm

class IndexView(View):
    form_class = BlacklistForm
    template_name = 'blacklist/blacklist_index.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'blacklist': get_items(), 'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            regex = form.cleaned_data['regex']
            ip = form.cleaned_data['ip']
            host = form.cleaned_data['host']
            if regex or ip or host:
                if regex:
                    add_item('regex:' + regex)
                if ip:
                    add_item('ip:' + ip)
                if host:
                    add_item('host:' + host)
            else:
                for field in form.data:
                    if field.startswith('delete-'):
                        line = int(field.split('delete-')[1])
                        delete_item(line)
            return HttpResponseRedirect('/blacklist/')

        return render(request, self.template_name, {'blacklist': get_items(), 'form': form})

def get_items():
    if hasattr(settings, 'BLACKLIST_FILE'):
        blacklist_file = settings.BLACKLIST_FILE
        with open(blacklist_file, 'r') as f:
            blacklist = f.readlines()
    else:
        with connections['blacklist'].cursor() as c:
            c.execute('SELECT item FROM blacklist')
            blacklist = [item[0] for item in c.fetchall()]

    return blacklist

def add_item(item):
    if hasattr(settings, 'BLACKLIST_FILE'):
        blacklist_file = settings.BLACKLIST_FILE
        with open(blacklist_file, 'a') as f:
            f.write(item + '\n')
    else:
        with connections['blacklist'].cursor() as c:
            c.execute('INSERT INTO blacklist VALUES (%s)', [item])

def delete_item(line):
    blacklist = get_items()

    if hasattr(settings, 'BLACKLIST_FILE'):
        blacklist_file = settings.BLACKLIST_FILE
        with open(blacklist_file, 'w') as f:
            for idx, item in enumerate(blacklist):
                if idx != line:
                    f.write(item)
    else:
        with connections['blacklist'].cursor() as c:
            c.execute('DELETE FROM blacklist WHERE item = %s', [blacklist[line]])

