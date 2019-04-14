from django.test import TestCase
from django.conf.urls import url
from django.shortcuts import HttpResponse,render,redirect
from django.utils.safestring import mark_safe
from django.forms import ModelForm
from .pager import Pagination
from django.db.models import Q
from django.db.models.fields.related import ManyToManyField,ForeignKey
import copy
from django.forms.models import ModelChoiceField


# Create your tests here.
class ModelStark(object):
    list_display=["__str__"]
    list_display_link=[]
    list_search=[]
    list_filter=[]
    actions=[]
    def __init__(self,model):
        self.model=model
    def setCheck(self,obj=None,header=False):
        if header:
            return mark_safe('<input id="choice" type="checkbox"')
        return mark_safe('<input class="item" name="selected_pk" value="%s" type="checkbox"'%obj.pk)

    def edit(self,obj=None,header=False):
        if header:
            return "操作"
        return mark_safe('<a href="%s/change/">编辑</a>'%obj.pk)
    def delete(self,obj=None,header=False):
        if header:
            return "操作"
        return mark_safe('<a href="%s/delete/">删除</a>'%obj.pk)
    @property
    def get_urls2(self):
        return self.get_urls_2(),None,None
    def get_urls_2(self):
        temp=[]
        temp.append(url(r'^$', self.list_view))
        temp.append(url(r'^add/$', self.add_view))
        temp.append(url(r'^(\d+)/change/$', self.change_view))
        temp.append(url(r'^(\d+)/delete/$', self.delete_view))
        return temp
    @property
    def new_list_display(self):
        temp=[]
        temp.append(ModelStark.setCheck)
        temp.extend(self.list_display)
        if not self.list_display_link:
            temp.append(ModelStark.edit)
        temp.append(ModelStark.delete)
        return temp



    def list_view(self, request):
        if request.method=="POST":
            print(request.POST)
            action=request.POST.get("action")
            selected_pk=request.POST.getlist("selected_pk")
            func=getattr(self,action)
            queryset=self.model.objects.filter(id__in=selected_pk)
            func(request,queryset)
        key_word=request.GET.get("q")
        q = Q()
        q.connector = "or"
        if key_word:
            for i in self.list_search:

                q.children.append((i+"__contains",key_word))
        filter_q=Q()
        filter_q.connector="and"
        for filter_field,val in request.GET.items():
            if filter_field in self.list_filter:
                filter_q.children.append((filter_field,val))
        data_list=self.model.objects.all().filter(q).filter(filter_q)
        showlist=ShowList(self,data_list,request)
        header_list=showlist.get_header()
        new_data_list=showlist.get_body()
        return render(request,"list_view.html",locals())
    def add_view(self,request):

        class FormDemo(ModelForm):
            class Meta:
                model=self.model
                fields="__all__"

        form = FormDemo()
        for bfield in form:
            if isinstance(bfield.field,ModelChoiceField):
                bfield.is_pop=True
                model_name=bfield.field.queryset.model._meta.model_name
                app_label=bfield.field.queryset.model._meta.app_label
                url_="/Stark/%s/%s/add"%(app_label,model_name)
                bfield.url_=url_+"?public_id=id_%s"%model_name

        if request.method=="POST":
            form=FormDemo(request.POST)
            if form.is_valid():
                obj=form.save()
                public_id = request.GET.get("public_id")
                if public_id:
                    id=obj.pk
                    title=str(obj)
                    return render(request,"pop.html",locals())
                else:
                    return redirect(self.create_url())
        return render(request,'add_view.html',locals())
    def create_url(self):
        app_name = self.model._meta.app_label
        model_name = self.model._meta.model_name
        _url = "/Stark/%s/%s/" % (app_name, model_name)
        return _url


    def change_view(self, request, arg):
        class FormDemo(ModelForm):
            class Meta:
                model=self.model
                fields="__all__"
        obj=self.model.objects.filter(id=int(arg)).first()
        if request.method=="POST":
            form=FormDemo(request.POST,instance=obj)
            if form.is_valid():
                form.save()
                return redirect(self.create_url())
            return render(request, 'edit_view.html', locals())


        form = FormDemo(instance=obj)
        return render(request,"edit_view.html",locals())

    def delete_view(self, request, arg):
        url_=self.create_url()
        if request.method=="POST":
            self.model.objects.filter(id=arg).delete()
            return redirect(url_)
        return render(request,'delete_view.html',locals())


class ShowList(object):
    def __init__(self,confg,data_list,request):
        self.confg=confg
        self.data_list=data_list
        self.request=request
        #分页
        all_count=self.data_list.count()
        current_page=int(self.request.GET.get("page",1))
        base_url=self.request.path
        self.pager=Pagination(current_page,all_count,base_url,self.request.GET,per_page_num=10,pager_count=10)
        self.page_data=self.data_list[self.pager.start:self.pager.end]
        self.actions=self.confg.actions
    def get_filter_linktages(self):
        temp={}
        for i in self.confg.list_filter:
            params=copy.deepcopy(self.request.GET)
            cid=self.request.GET.get(i,0)
            field=self.confg.model._meta.get_field(i)
            if isinstance(field,ForeignKey) or isinstance(field,ManyToManyField):
                data_list = field.rel.to.objects.all()
            else:
                data_list=self.confg.model.objects.all().values("pk",i)
            ret=[]
            if i in params:
                del params[i]
            _url=params.urlencode()
            ret.append('<a href="?%s">全部</a>'%_url)

            for obj in data_list:
                if isinstance(field, ForeignKey) or isinstance(field, ManyToManyField):
                    pk=obj.pk
                    text=str(obj)
                    params[i] = pk
                else:
                    pk=obj.get("pk")
                    text=obj.get(i)
                    params[i]=text

                _url=params.urlencode()
                if cid==str(pk) or cid==text:
                    link_tag="<a class='show' href='?%s'>%s</a>"%(_url,text)
                else:
                    link_tag = "<a href='?%s'>%s</a>" % (_url, text)
                ret.append(link_tag)
            temp[i]=ret

        return temp
    def get_action_list(self):
        temp=[]
        for action in self.actions:
            temp.append({
                "name":action.__name__,
                "desc":action.short_description
            })
        return temp
    def get_header(self):
        header_list = []
        for i in self.confg.new_list_display:
            if callable(i):
                val = i(self.confg, header=True)
                header_list.append(val)
            else:
                if i == "__str__":
                    header_list.append(self.confg.model._meta.model_name)
                else:
                    var = self.confg.model._meta.get_field(i).verbose_name
                    header_list.append(var)
        return header_list
    def get_body(self):
        new_data_list = []
        for obj in self.page_data:
            temp = []
            for i in self.confg.new_list_display:
                if isinstance(i, str):
                    if i=="__str__":
                        val=getattr(obj, i)
                    elif isinstance(self.confg.model._meta.get_field(i),ManyToManyField):
                        t=[]
                        ret=getattr(obj,i).all()
                        for obj in ret:
                            t.append(str(obj))
                        val=",".join(t)
                    else:
                        val = getattr(obj, i)
                    if i in self.confg.list_display_link:
                        var = mark_safe('<a href="%s/change/">%s</a>' % (obj.pk, val))
                        temp.append(var)
                    else:
                        temp.append(val)
                else:
                    val = i(self.confg, obj)
                    temp.append(val)
            new_data_list.append(temp)
        return new_data_list
class StarkSite(object):
    def __init__(self):
        self._registry={}
    def register(self, model, admin_class=None, **options):
        if not admin_class:
            admin_class=ModelStark
        self._registry[model]=admin_class(model)
    def get_urls(self):
        temp=[]
        for model,stark_class_obj in self._registry.items():
            app_name = model._meta.app_label
            model_name=model._meta.model_name
            temp.append(url(r'^{0}/{1}/'.format(app_name,model_name),stark_class_obj.get_urls2))
        return temp
    @property
    def urls(self):
        return self.get_urls(),None,None

site=StarkSite()



