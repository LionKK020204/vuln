from django.shortcuts import render, redirect
from django.db import connection
from django.http import HttpResponse
from django.utils.html import escape
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os


def dictfetchall(cursor):
    # Helper: convert query result sang list dict cho dễ render
    desc = cursor.description
    return [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]



def search(request):
    rows = []
    search_name = ''
    executed_query = ''

    if request.method == 'POST':
        search_name = request.POST.get('search_name', '')

        # ---------------- VULNERABLE ----------------
        # LỖI:
        # - Nối trực tiếp input user vào câu SQL
        # - Attacker có thể chèn payload SQL (OR 1=1, UNION, ...)

        # executed_query = (
        #     "SELECT id, ma_sv, ten_sv, dia_chi, lop "
        #     "FROM student WHERE ten_sv LIKE '%" + search_name + "%' "
        #     "ORDER BY id DESC"
        # )
        # with connection.cursor() as cursor:
        #     cursor.execute(executed_query)
        #     rows = dictfetchall(cursor)
        # ---------------- FIX ----------------
        # CÁCH SỬA:
        # - Dùng placeholder (%s)
        # - DB driver tự escape input => chặn SQL Injection
        #
        executed_query = """
            SELECT id, ma_sv, ten_sv, dia_chi, lop
            FROM student
            WHERE ten_sv LIKE %s
            ORDER BY id DESC
        """
        with connection.cursor() as cursor:
            cursor.execute(executed_query, [f"%{search_name}%"])
            rows = dictfetchall(cursor)

    return render(request, 'search.html', {
        'rows': rows,
        'search_name': search_name,
        'executed_query': executed_query
    })



def echo(request):
    q = request.GET.get('q', '')

    # ---------------- VULNERABLE ----------------
    # LỖI:
    # - Render trực tiếp input user ra HTML
    # - Trình duyệt sẽ thực thi <script>, <img onerror>, ...
    # if q:
    #     return HttpResponse(
    #         f"<html><body>"
    #         f"<h3>Reflected (vulnerable)</h3>"
    #         f"<div>{q}</div>"
    #         f"</body></html>"
    #     )
    #
    # return render(request, 'echo.html', {'q': ''})

    # ---------------- FIX ----------------
    # CÁCH SỬA:
    # - Escape toàn bộ input trước khi render
    # - Biến script thành text, không cho chạy
    #
    safe_q = escape(q)
    return render(request, 'echo.html', {'q': safe_q})





def upload_file(request):
    msg = ''
    file_url = ''

    if request.method == 'POST' and request.FILES.get('file'):
        f = request.FILES['file']

        # ---------------- VULNERABLE ----------------
        # LỖI:
        # - Không kiểm tra loại file
        # - Không kiểm tra tên file
        # - Có thể upload webshell / file độc hại
        upload_path = os.path.join(settings.MEDIA_ROOT, f.name)
        with open(upload_path, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)
        file_url = settings.MEDIA_URL + f.name
        msg = 'Upload successful (VULNERABLE)'

        # ---------------- FIX ----------------
        # CÁCH SỬA:
        # - Whitelist extension
        # - Dùng FileSystemStorage để tránh path traversal
        #
        # allowed_ext = ['.jpg', '.png', '.pdf', '.txt']
        # ext = os.path.splitext(f.name)[1].lower()
        #
        # if ext not in allowed_ext:
        #     msg = 'File type not allowed'
        # else:
        #     fs = FileSystemStorage(location=settings.MEDIA_ROOT)
        #     filename = fs.save(f.name, f)
        #     file_url = settings.MEDIA_URL + filename
        #     msg = 'Upload successful'

    return render(request, 'upload.html', {
        'msg': msg,
        'file_url': file_url
    })


# ============================================================
# LOGIN – SQL INJECTION
# ============================================================
def login_view(request):
    msg = ''

    if request.method == 'POST':
        u = request.POST.get('username', '')
        p = request.POST.get('password', '')

        # ---------------- VULNERABLE ----------------
        # LỖI:
        # - Login query nối chuỗi
        # - Có thể bypass login bằng SQL Injection
        q = "SELECT id FROM admin_user WHERE username = '" + u + "' AND password = '" + p + "'"
        with connection.cursor() as cursor:
            cursor.execute(q)
            row = cursor.fetchone()

        # ---------------- FIX ----------------
        # CÁCH SỬA:
        # - Bind param cho username & password
        #
        # q = "SELECT id FROM admin_user WHERE username = %s AND password = %s"
        # with connection.cursor() as cursor:
        #     cursor.execute(q, [u, p])
        #     row = cursor.fetchone()

        if row:
            request.session['admin'] = u
            return redirect('student_list')
        else:
            msg = 'Invalid credentials'

    return render(request, 'login.html', {'msg': msg})


def logout_view(request):
    request.session.flush()
    return redirect('search')


def require_login(fn):
    def wrapper(request, *args, **kwargs):
        # Chỉ check session cho demo
        if not request.session.get('admin'):
            return redirect('login')
        return fn(request, *args, **kwargs)
    return wrapper



@require_login
def student_list(request):
    executed_query = "SELECT id, ma_sv, ten_sv, dia_chi, lop FROM student ORDER BY id DESC"
    with connection.cursor() as cursor:
        cursor.execute(executed_query)
        rows = dictfetchall(cursor)

    return render(request, 'student_list.html', {
        'rows': rows,
        'executed_query': executed_query,
        'admin': request.session.get('admin')
    })


@require_login
def student_add(request):
    if request.method == 'POST':
        ma_sv = request.POST.get('ma_sv', '')
        ten_sv = request.POST.get('ten_sv', '')
        dia_chi = request.POST.get('dia_chi', '')
        lop = request.POST.get('lop', '')

        # ---------------- VULNERABLE ----------------
        # LỖI:
        # - Insert dùng string format
        # - Inject được qua form
        q = (
            "INSERT INTO student (ma_sv, ten_sv, dia_chi, lop) "
            f"VALUES ('{ma_sv}','{ten_sv}','{dia_chi}','{lop}')"
        )
        with connection.cursor() as cursor:
            cursor.execute(q)

        # ---------------- FIX ----------------
        # CÁCH SỬA:
        # - Insert bằng placeholder
        #
        # q = """
        #     INSERT INTO student (ma_sv, ten_sv, dia_chi, lop)
        #     VALUES (%s, %s, %s, %s)
        # """
        # with connection.cursor() as cursor:
        #     cursor.execute(q, [ma_sv, ten_sv, dia_chi, lop])

        return redirect('student_list')

    return render(request, 'student_form.html', {'action': 'Add', 'student': None})


@require_login
def student_edit(request, id):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT id, ma_sv, ten_sv, dia_chi, lop FROM student WHERE id = {id}")
        row = cursor.fetchone()

    if not row:
        return HttpResponse('Student not found', status=404)

    cols = [c[0] for c in cursor.description]
    student = dict(zip(cols, row))

    if request.method == 'POST':
        ma_sv = request.POST.get('ma_sv', '')
        ten_sv = request.POST.get('ten_sv', '')
        dia_chi = request.POST.get('dia_chi', '')
        lop = request.POST.get('lop', '')

        # ---------------- VULNERABLE ----------------
        # LỖI:
        # - Update concat string
        # - Inject qua field hoặc id
        qup = (
            f"UPDATE student SET ma_sv='{ma_sv}', ten_sv='{ten_sv}', "
            f"dia_chi='{dia_chi}', lop='{lop}' WHERE id={id}"
        )
        with connection.cursor() as cursor:
            cursor.execute(qup)

        # ---------------- FIX ----------------
        # CÁCH SỬA:
        # - Bind param cho toàn bộ giá trị
        #
        # qup = """
        #     UPDATE student
        #     SET ma_sv=%s, ten_sv=%s, dia_chi=%s, lop=%s
        #     WHERE id=%s
        # """
        # with connection.cursor() as cursor:
        #     cursor.execute(qup, [ma_sv, ten_sv, dia_chi, lop, id])

        return redirect('student_list')

    return render(request, 'student_form.html', {'action': 'Edit', 'student': student})



@require_login
def student_delete(request, id):

    # ---------------- VULNERABLE ----------------
    # LỖI:
    # - id nối trực tiếp vào SQL
    # - Có thể inject qua URL
    with connection.cursor() as cursor:
        cursor.execute(f"DELETE FROM student WHERE id={id}")

    # ---------------- FIX ----------------
    # CÁCH SỬA:
    # - Bind param cho id
    #
    # with connection.cursor() as cursor:
    #     cursor.execute("DELETE FROM student WHERE id=%s", [id])

    return redirect('student_list')
