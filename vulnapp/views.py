from django.shortcuts import render, redirect
from django.db import connection
from django.http import HttpResponse

def dictfetchall(cursor):
    desc = cursor.description
    return [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]

# ---------------- Public search (VULNERABLE SQLi) ----------------
def search(request):
    rows = []
    search_name = ''
    executed_query = ''
    if request.method == 'POST':
        search_name = request.POST.get('search_name', '')
        # ----- VULNERABLE on purpose: string concatenation (SQL injection demo) -----
        executed_query = "SELECT id, ma_sv, ten_sv, dia_chi, lop FROM student WHERE ten_sv LIKE '%" + search_name + "%' ORDER BY id DESC"
        with connection.cursor() as cursor:
            cursor.execute(executed_query)
            rows = dictfetchall(cursor)
    return render(request, 'search.html', {
        'rows': rows,
        'search_name': search_name,
        'executed_query': executed_query
    })

# ---------------- Reflected XSS endpoint (vulnerable) ----------------

def echo(request):
    q = request.GET.get('q', '')
    if q:
        # VULNERABLE (for testing only):
        # Return raw HTML with user input inserted directly — Python-level reflected XSS sink.
        return HttpResponse(f"<html><body>"
                            f"<h3>Reflected (vulnerable)</h3>"
                            f"<div>{q}</div>"
                            f"</body></html>")
    # If no param provided, show the form (so user can input in the UI)
    return render(request, 'echo.html', {'q': ''})

# ---------------- Simple vulnerable login ----------------
def login_view(request):
    msg = ''
    if request.method == 'POST':
        u = request.POST.get('username', '')
        p = request.POST.get('password', '')
        # ----- VULNERABLE login (raw SQL) -----
        q = "SELECT id FROM admin_user WHERE username = '" + u + "' AND password = '" + p + "'"
        with connection.cursor() as cursor:
            try:
                cursor.execute(q)
                row = cursor.fetchone()
                if row:
                    request.session['admin'] = u
                    return redirect('student_list')
                else:
                    msg = 'Invalid credentials'
            except Exception as e:
                msg = f'Error: {e}'
    return render(request, 'login.html', {'msg': msg})

def logout_view(request):
    request.session.flush()
    return redirect('search')

# ---------------- Simple decorator for admin pages ----------------
def require_login(fn):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('admin'):
            return redirect('login')
        return fn(request, *args, **kwargs)
    return wrapper

# ---------------- Students management (protected) ----------------
@require_login
def student_list(request):
    rows = []
    executed_query = ''
    with connection.cursor() as cursor:
        executed_query = "SELECT id, ma_sv, ten_sv, dia_chi, lop FROM student ORDER BY id DESC"
        cursor.execute(executed_query)
        rows = dictfetchall(cursor)
    return render(request, 'student_list.html', {'rows': rows, 'executed_query': executed_query, 'admin': request.session.get('admin')})

@require_login
def student_add(request):
    if request.method == 'POST':
        ma_sv = request.POST.get('ma_sv','').replace("'", "''")
        ten_sv = request.POST.get('ten_sv','').replace("'", "''")
        dia_chi = request.POST.get('dia_chi','').replace("'", "''")
        lop = request.POST.get('lop','').replace("'", "''")
        # VULNERABLE insert (string concat) - demo only
        q = "INSERT INTO student (ma_sv, ten_sv, dia_chi, lop) VALUES ('%s','%s','%s','%s')" % (ma_sv, ten_sv, dia_chi, lop)
        with connection.cursor() as cursor:
            cursor.execute(q)
        return redirect('student_list')
    return render(request, 'student_form.html', {'action': 'Add', 'student': None})

@require_login
def student_edit(request, id):
    student = None
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT id, ma_sv, ten_sv, dia_chi, lop FROM student WHERE id = {id}")
        row = cursor.fetchone()
        if row:
            cols = [c[0] for c in cursor.description]
            student = dict(zip(cols, row))
        else:
            return HttpResponse('Student not found', status=404)
    if request.method == 'POST':
        ma_sv = request.POST.get('ma_sv','').replace("'", "''")
        ten_sv = request.POST.get('ten_sv','').replace("'", "''")
        dia_chi = request.POST.get('dia_chi','').replace("'", "''")
        lop = request.POST.get('lop','').replace("'", "''")
        # VULNERABLE update
        qup = f"UPDATE student SET ma_sv='{ma_sv}', ten_sv='{ten_sv}', dia_chi='{dia_chi}', lop='{lop}' WHERE id={id}"
        with connection.cursor() as cursor:
            cursor.execute(qup)
        return redirect('student_list')
    return render(request, 'student_form.html', {'action': 'Edit', 'student': student})

@require_login
def student_delete(request, id):
    with connection.cursor() as cursor:
        cursor.execute(f"DELETE FROM student WHERE id={id}")
    return redirect('student_list')



# #vulnapp/views.py (fixed: parameterized queries + no Python-level XSS sinks)
# from functools import wraps
# from django.shortcuts import render, redirect
# from django.db import connection
# from django.http import HttpResponse, HttpResponseRedirect
# from django.urls import reverse
# from django.contrib import messages
#
# def dictfetchall(cursor):
#     desc = cursor.description
#     return [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
#
# # ---------------- Public search (SAFE: parameterized) ----------------
# def search(request):
#     rows = []
#     search_name = ''
#     executed_query = ''
#     if request.method == 'POST':
#         search_name = request.POST.get('search_name', '').strip()
#         # SAFE: use parameterized query (no string concatenation)
#         executed_query = "SELECT id, ma_sv, ten_sv, dia_chi, lop FROM student WHERE ten_sv LIKE %s ORDER BY id DESC"
#         params = [f"%{search_name}%"]
#         with connection.cursor() as cursor:
#             cursor.execute(executed_query, params)
#             rows = dictfetchall(cursor)
#     return render(request, 'search.html', {
#         'rows': rows,
#         'search_name': search_name,
#         'executed_query': executed_query
#     })
#
# # ---------------- Reflected XSS endpoint (SAFE) ----------------
# # Note: we intentionally do NOT return raw user input in HttpResponse.
# # Template must use {{ q }} (auto-escaped). Do NOT use {{ q|safe }}.
# def echo(request):
#     q = request.GET.get('q', '')
#     # Render the template and let Django auto-escape the value.
#     return render(request, 'echo.html', {'q': q})
#
# # ---------------- Simple safe login (parameterized) ----------------
# def login_view(request):
#     msg = ''
#     if request.method == 'POST':
#         u = request.POST.get('username', '').strip()
#         p = request.POST.get('password', '').strip()
#         # SAFE: parameterized query
#         q = "SELECT id FROM admin_user WHERE username = %s AND password = %s"
#         with connection.cursor() as cursor:
#             try:
#                 cursor.execute(q, [u, p])
#                 row = cursor.fetchone()
#                 if row:
#                     request.session['admin'] = u
#                     return redirect('student_list')
#                 else:
#                     msg = 'Invalid credentials'
#             except Exception as e:
#                 # log/notify in dev; show generic message
#                 msg = 'Login error'
#                 # optionally: messages.error(request, f'Login error: {e}')
#     return render(request, 'login.html', {'msg': msg})
#
# def logout_view(request):
#     request.session.flush()
#     return redirect('search')
#
# # ---------------- simple decorator for admin pages ----------------
# def require_login(fn):
#     @wraps(fn)
#     def wrapper(request, *args, **kwargs):
#         if not request.session.get('admin'):
#             return redirect('login')
#         return fn(request, *args, **kwargs)
#     return wrapper
#
# # ---------------- Students management (protected, safe SQL) ----------------
# @require_login
# def student_list(request):
#     rows = []
#     executed_query = "SELECT id, ma_sv, ten_sv, dia_chi, lop FROM student ORDER BY id DESC"
#     with connection.cursor() as cursor:
#         cursor.execute(executed_query)
#         rows = dictfetchall(cursor)
#     return render(request, 'student_list.html', {'rows': rows, 'executed_query': executed_query, 'admin': request.session.get('admin')})
#
# @require_login
# def student_add(request):
#     if request.method == 'POST':
#         ma_sv = request.POST.get('ma_sv', '').strip()
#         ten_sv = request.POST.get('ten_sv', '').strip()
#         dia_chi = request.POST.get('dia_chi', '').strip()
#         lop = request.POST.get('lop', '').strip()
#         q = "INSERT INTO student (ma_sv, ten_sv, dia_chi, lop) VALUES (%s, %s, %s, %s)"
#         with connection.cursor() as cursor:
#             cursor.execute(q, [ma_sv, ten_sv, dia_chi, lop])
#         return redirect('student_list')
#     return render(request, 'student_form.html', {'action': 'Add', 'student': None})
#
# @require_login
# def student_edit(request, id):
#     student = None
#     with connection.cursor() as cursor:
#         cursor.execute("SELECT id, ma_sv, ten_sv, dia_chi, lop FROM student WHERE id = %s", [id])
#         row = cursor.fetchone()
#         if row:
#             cols = [c[0] for c in cursor.description]
#             student = dict(zip(cols, row))
#         else:
#             return HttpResponse('Student not found', status=404)
#
#     if request.method == 'POST':
#         ma_sv = request.POST.get('ma_sv', '').strip()
#         ten_sv = request.POST.get('ten_sv', '').strip()
#         dia_chi = request.POST.get('dia_chi', '').strip()
#         lop = request.POST.get('lop', '').strip()
#         qup = "UPDATE student SET ma_sv=%s, ten_sv=%s, dia_chi=%s, lop=%s WHERE id=%s"
#         with connection.cursor() as cursor:
#             cursor.execute(qup, [ma_sv, ten_sv, dia_chi, lop, id])
#         return redirect('student_list')
#
#     return render(request, 'student_form.html', {'action': 'Edit', 'student': student})
#
# @require_login
# def student_delete(request, id):
#     with connection.cursor() as cursor:
#         cursor.execute("DELETE FROM student WHERE id=%s", [id])
#     return redirect('student_list')
