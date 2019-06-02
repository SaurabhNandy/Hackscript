from django.shortcuts import render,redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from .forms import DocumentForm,CommentForm
import convertapi,json,os
from .models import Document
from rossum.extraction import ElisExtractionApi
from django.http import JsonResponse
from hacks import settings as s

def home(request):
    if request.method == 'POST' and request.FILES:
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            name = request.FILES['document'].name 
            name = name.replace(' ','_')
            convert(name)
            context=extract_data()
            print(context)
            return render(request,'extract/home.html',{ 'form':form,'context': context})
    else:
        form = DocumentForm()
    return render(request,'extract/home.html',{ "form": form }) 


def about(request):
    return render(request,'extract/about.html',{})


def contact(request):
    return render(request,'extract/contact.html',{})


def comment(request):
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            print("Done form....................")
            form.save()
            return render(request,'extract/contact.html',{"form": form})
    else:
        form = CommentForm()
    return render(request,'extract/contact.html',{ "form": form }) 



def convert(name):
    convertapi.api_secret =str(s.CONVERTAPIKEY)
    path = settings.MEDIA_ROOT+'\\documents\\' + name
    result = convertapi.convert('pdf', { 'File':path })
    result.file.save(settings.MEDIA_ROOT+'\\pdf.pdf')
    print("converted..............................")



def extract_data():
    api = ElisExtractionApi(s.ELISAPIKEY)
    extraction = api.extract(settings.MEDIA_ROOT+'\\pdf.pdf',settings.MEDIA_ROOT+'\\result.json')

    inp=json.load(open(settings.MEDIA_ROOT+'\\result.json','r'))
    my_dict={}
    t =""
    flag=0
    if inp.get("full_text"):
        for i in inp.get("full_text").get("content"):
            if(i.lower().find("po")!=-1 or (i.lower()).find("purchase order")!=-1):
                t = "PO"
                break
            else:
                flag+= 1
        if(flag>0 and t==""):
            t = "INVOICE"

    a=len(inp["fields"])
    my_dict["doctype"]=t
    for i in range(a):
        if (inp["fields"][i].get("title"))=="Supplier Name":
            my_dict["suppliercompany"]=inp["fields"][i].get("value")
        elif (inp["fields"][i].get("title"))=="Supplier Address":
            my_dict["supplieraddress"]=inp["fields"][i].get("value")
        elif (inp["fields"][i].get("title"))=="Recipient Name":
            my_dict["billto"]=inp["fields"][i].get("value")
        elif (inp["fields"][i].get("title"))=="Recipient Name":
            my_dict["shipto"]=inp["fields"][i].get("value")
        elif ((inp["fields"][i].get("title"))=="Order Number" or (inp["fields"][i].get("title"))=="Invoice Identifier"):
            my_dict["ordernum"]=inp["fields"][i].get("value")
        elif (inp["fields"][i].get("title"))=="Issue Date":
            my_dict["issuedate"]=inp["fields"][i].get("value")
        elif (inp["fields"][i].get("title"))=="Total Amount":
            my_dict["totalamount"]=inp["fields"][i].get("value")
        elif (inp["fields"][i].get("title"))=="Tax Total":
            my_dict["total tax"]=inp["fields"][i].get("value")
        elif (inp["fields"][i].get("title"))=="Terms":
            my_dict["terms"]=inp["fields"][i].get("value")
    #my_dict=json.dumps(my_dict)
    return my_dict