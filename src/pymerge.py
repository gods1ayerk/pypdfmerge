#!/usr/bin/python2
"""
MIT License

Copyright (c) 2018-present Sachet Khanal

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import PyPDF2, os, sys, json, base64, cgi, traceback, uuid, urllib
from cStringIO import StringIO

pdfPath = '/var/www/pdfs/'

def getMergeUUID():
	merge_id = str(uuid.uuid4())
	while os.path.exists(pdfPath+merge_id): merge_id = str(uuid.uuid4())
	os.makedirs(pdfPath+merge_id)
	return merge_id
	
def add_pdf(merge_id, pdf_stream):
	try:
		file_path = pdfPath+merge_id+'/'
		pdf_in = StringIO(pdf_stream)
		reader = PyPDF2.PdfFileReader(pdf_in)
		writer = PyPDF2.PdfFileWriter()
		count = 0
		for page_number in range(reader.getNumPages()):
			page = reader.getPage(page_number)
			count += 1
			if '{{end_even}}' in page.extractText():
				# Page ending indicator is in even page number implies odd number of pages, so add blank page to make even
				if (count%2)==0: writer.addBlankPage()
				count = 0
			else:
				writer.addPage(page)
		index = len([name for name in os.listdir(file_path)])
		pdf_name = str(index)+'.pdf'
		with open(file_path+pdf_name,'wb') as outputFile:
			writer.write(outputFile)
		returnResponse({'success':True, 'msg': 'PDF content successfully added to merge list.'})
	except:
		returnResponse({'success':False,'msg':'An unknown error occured. Please contact system adminitrator.','errorInfo':traceback.print_exc(file=sys.stdout)})
		
def merge(merge_id, merged_filename):
	try:
		file_path = pdfPath+merge_id+'/'
		file_count = len([name for name in os.listdir(file_path)])
		if os.path.exists(file_path+merged_filename):
			if file_count==1: 
				returnResponse({'success':True, 'msg': urllib.pathname2url(str(os.environ['HTTP_HOST'])+'/pdfs/'+merge_id+'/'+merged_filename)})
			else:
				returnResponse({'success':False, 'msg': 'File is being merged. Please wait for the operation to complete.'})
		else:
			merger = PyPDF2.PdfFileWriter()
			#merger = PyPDF2.PdfFileMerger()
			for filename in os.listdir(file_path):
				merger.appendPagesFromReader(PyPDF2.PdfFileReader(file_path+filename))
				#merger.append(PyPDF2.PdfFileReader(file(file_path+filename,'rb')))
			with open(file_path+merged_filename,'wb') as outputFile:
				merger.write(outputFile)
			#merger.write(file_path+merged_filename)
			for filename in os.listdir(file_path):
				if filename!=merged_filename: os.remove(file_path+filename)
			returnResponse({'success':True, 'msg': urllib.pathname2url(str(os.environ['HTTP_HOST'])+'/pdfs/'+merge_id+'/'+merged_filename)})
	except:
		returnResponse({'success':False,'msg':'Unknown error while merging','errorInfo':traceback.print_exc(file=sys.stdout)})

def returnResponse(response):
	print(json.JSONEncoder().encode(response))

def main():
	print('Content-type: application/json')
	print 
	try:
		form = cgi.FieldStorage()
		request_type = form['request_type'].value
		if 'merge_id' in request_type:
			returnResponse({'success':True, 'msg': getMergeUUID()}) 
		elif 'add_pdf' in request_type:
			base64data = form['data'].value
			merge_id = form['merge_id'].value
			data_stream = base64.decodestring(base64data)
			add_pdf(merge_id, data_stream)
		elif 'merge' in request_type:
			merge_id = form['merge_id'].value
			filename = form['filename'].value
			merge(merge_id, filename)
		else:
			returnResponse({'success':False, 'msg': 'Invalid request type.'})
	except KeyError:
		returnResponse({'success':False,'msg':'Missing required input data.'})
	except base64.binascii.Error:
		returnResponse({'success':False,'msg':'Invalid data. Data should be base64 encoded.'})
	except IOError as e:
		returnResponse({'success':False,'msg':str(e)})
	except:
		returnResponse({
			'success':False,
			'msg':'An unknown error has occured. Please contact system administrator.',
			'errorInfo':traceback.print_exc(file=sys.stdout)
		})

main()
