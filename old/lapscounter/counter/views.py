from django.http import HttpResponse

template = '''
<html>
<body>
<style>
  C {{
     font-size: 600px;
     color: {};
  }}
  B {{
     font-size: 30px
  }}
  input.button {{
    -webkit-appearance: button;
    -moz-appearance: button;
    appearance: button;
    text-decoration: none;
    color: gray;
  }}
</style>
<form name='command'>
<table border=2>
<th><td><B><input onclick='v=document.command.start_button.value; if (v=="Stop") document.command.start_button.value="Start"; else document.command.start_button.value="Stop";' id='start_button' type='button' value='Start'/></B></td><td><B><button>Reset</button></B></td></th>
<tr><td colspan=4><C>{}</C></td></tr>
</table>
</form>
</body>
</html>
'''

def index(request):
    page = template.format('red','0000')
    return HttpResponse(page)
