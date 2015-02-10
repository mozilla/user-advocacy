from jinja2 import Environment, FileSystemLoader, Template
import markdown 
import sys
import getopt
import os
import re
import codecs
import textwrap

def main(argv):

# Default values for various files
    inputfile = '../md/index.md'
    outputfile = 'index.html'
    project = 'default'

# Read arguments
    
    try:
        opts, args = getopt.getopt(argv,"hi:p:o:",["infile=","project=","outfile="])
    except getopt.GetoptError:
        print 'markdown2html.py -i <inputfile> -p <project name> -o <outputfile>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'Usage: markdown2html.py -i <inputfile> -p <projectname> -o <outputfile>'
            sys.exit()
        elif opt in ("-i", "--infile"):
            inputfile = arg
        elif opt in ("-o", "--outfile"):
            outputfile = arg
        elif opt in ("-p", "--project"):
            project = arg
    reportname = re.sub(r'\.md|\.markdown$', '', os.path.basename(inputfile))
    
    file = open(inputfile, 'r')
    markdown_content = file.read()
    
# Load templates and files
    env = Environment(loader=FileSystemLoader('../templates'))
    templatefile = project + '.html'
    try:
        template = env.get_template(templatefile)
    except TemplateNotFound:
        template = env.get_template('default.html')
       
    try:
        os.mkdir('../../../www/reports/' + project + '/' + reportname)
        os.chmod('../../../www/reports/' + project + '/' + reportname, 0777)
    except OSError:
        pass
    with open('../../../www/reports/' + project + '/' + reportname + '/index.html', 'w') as out_file:
        out_file.write(convert_md(md_content, template))
        os.chmod('../../../www/reports/' + project + '/' + reportname + '/index.html', 0774)
    

def convert_md(markdown_content, template, **kwargs):
    in_bq = False
    in_cite = False
    text = ''
    link = ''
    markdown_text = ''
    in_metadata = False
    first_line = True
    found_content_start = False
    for line in iter(markdown_content.splitlines()):
        if first_line:
            if not re.search(r'\S', line):
                continue
            first_line = False
            if re.match(r'\w+:', line):
                in_metadata = True
        if in_metadata:
            if re.match(r'\w+:|\s{4,}', line):
                markdown_text += line + "\n"
                continue 
            in_metadata = False
        if not in_metadata:
            if not found_content_start:
                if re.search(r'\S', line):
                    found_content_start = True
                    if not re.match(r'#', line):
                        markdown_text += "###### REMOVE ME NOW NOW NOW\n"
            if in_cite:
                if not re.match('^\s*>', line):
                    markdown_text = remove_last_line(markdown_text)
                    markdown_text += \
                            '\n<div class="citation"><a href="%s">%s</a></div>\n' \
                            % (link, text)
                in_cite = False
                in_bq = False
            line = re.sub(r'(\bbug\s\s?\#?(\d{5,9}))', r'[\1](https://bugzil.la/\2)', line, flags=re.I)
            
            line = re.sub(r'^(\s*\##+)\+(.*)$', r'\g<1>\g<2> {:class=expand}', line)
            
            markdown_text += line + "\n"
            if in_bq:
                match = re.match('^\s*>\s*\[([^\[]+)\]\((.+)\)\s*$', line)
                if match:
                    in_cite = True
                    text = match.group(1)
                    link = match.group(2)
                elif re.match('^\s*$', line):
                    line.strip("\n")
                    markdown_text += line + "\n<!-- -->\n"
                in_bq = False
            if re.match('^\s*>', line):
                in_bq = True
    if in_cite:
        markdown_text = remove_last_line(markdown_text)
        markdown_text += \
                '\n<div class="citation"><a href="%s">%s</a></div>\n' \
                % (link, text)

# Generate markdown object and process
    extensions = ['tables', 'smart_strong', 'meta', 'smarty',
        'sane_lists', 'outline', 'toc', 'attr_list', 'footnotes']
    extension_configs = { 'footnotes':
                            [ ('BACKLINK_TEXT','[back]')]
                        }
    md = markdown.Markdown(extensions = extensions, extension_configs = extension_configs,
        output_format = 'html5')
    html_text = md.convert(markdown_text)
    html_text = html_text.replace('<h6 id="remove-me-now-now-now">REMOVE ME NOW NOW NOW</h6>','')
    html_text = html_text.replace('<!-- -->\n', '')
    
    html_text = re.sub('<h(?P<num>[2-9]).*?>\+?</h(?P=num)>','',html_text,0,re.I)
    
    footnote_replace = textwrap.dedent("""\
    </section>
    <section id="footnote-section">
    <h4>Footnotes</h4>
    \g<1>
    """)
    html_text = re.sub('<div class="footnote">\s*<hr>\s*(.*)</div>',footnote_replace, html_text,0, re.S)
    
    
    parameters = kwargs;
    for param, value in md.Meta.iteritems():
        if len(value) <= 2:
            parameters[param] = value[0]
        else:
            parameters[param] = value

# Finally return
    return template.render(content=html_text, toc=md.toc, **parameters)

def convert_md_str_template(markdown_content, template_content, **kwargs):
    template = Template(template_content)
    return convert_md(markdown_content, template, **kwargs)
    
    
def get_md_meta(markdown_content):
# This is probably overkill but we're trying to do the same thing as our normal
# markdown parser but only grab the metadata.
    markdown_text = ''
    in_metadata = False
    first_line = True
    found_content_start = False
    for line in iter(markdown_content.splitlines()):
        if first_line:
            if not re.search(r'\S', line):
                continue
            first_line = False
            if re.match(r'\w+:', line):
                in_metadata = True
        if in_metadata:
            if re.match(r'\w+:|\s{4,}', line):
                markdown_text += line + "\n"
                continue 
            in_metadata = False
        if not in_metadata:
            break
# Generate markdown object and process
    extensions = ['tables', 'smart_strong', 'meta', 'smarty',
        'sane_lists', 'outline', 'toc', 'attr_list', 'footnotes']
    md = markdown.Markdown(extensions = extensions, output_format = 'html5')
    html_text = md.convert(markdown_text)
    parameters = {};
    for param, value in md.Meta.iteritems():
        if len(value) <= 2:
            parameters[param] = value[0]
        else:
            parameters[param] = value
    return parameters
    
def remove_last_line(s):
    
    return s[:s.rfind('\n',0,-1)+1]

if __name__ == "__main__":
   main(sys.argv[1:])
