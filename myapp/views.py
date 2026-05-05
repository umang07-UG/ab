from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from functools import wraps
import os
import json
from django.views.decorators.http import require_POST
from .models import User, Chat, Message


def custom_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.session.get('is_logged_in'):
            return view_func(request, *args, **kwargs)
        return redirect('login')
    return wrapper


def index(request):
    return render(request, 'index.html')


def home(request):
    user = None
    email = request.session.get('email')

    if email:
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            request.session.flush()

    return render(request, 'home.html', {'user': user})


def signup(request):
    if request.method == "POST":
        name      = request.POST.get('name', '').strip()
        email     = request.POST.get('email', '').strip()
        mobile    = request.POST.get('mobile', '').strip()
        password  = request.POST.get('password', '')
        cpassword = request.POST.get('cpassword', '')
        profile_image = request.FILES.get('profile_image')

        if not name or not email or not password:
            return render(request, 'signup.html', {'msg': "Name, email and password are required"})

        if User.objects.filter(email=email).exists():
            return render(request, 'signup.html', {'msg': "Email already exists"})

        if password != cpassword:
            return render(request, 'signup.html', {'msg': "Password and Confirm Password do not match"})

        try:
            mobile_int = int(mobile) if mobile else 0
        except ValueError:
            return render(request, 'signup.html', {'msg': "Mobile number must be numeric"})

        try:
            user = User(
                name=name,
                email=email,
                mobile=mobile_int,
                password=password,
            )
            if profile_image:
                user.profile_image = profile_image
            user.save()
        except Exception as e:
            return render(request, 'signup.html', {'msg': f"Account creation failed: {str(e)}"})

        return render(request, 'login.html', {'msg': "Sign Up Done"})

    return render(request, 'signup.html')


def signup_desh(request):
    return render(request, 'signup_desh.html')


@csrf_exempt
def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)

            if user.password == password:
                request.session['email'] = user.email
                request.session['profile'] = user.profile_image.url if user.profile_image else ''
                request.session['is_logged_in'] = True
                request.session['user_id'] = user.id
                return redirect('home')

            return render(request, 'login.html', {'msg': "Password doesn't match"})

        except User.DoesNotExist:
            return render(request, 'login.html', {'msg': "Email doesn't exist"})

    return render(request, 'login.html')


def logout_view(request):
    request.session.flush()
    return redirect('login')


@custom_login_required
def main(request):
    return render(request, 'main.html')


@custom_login_required
def chat(request):
    email = request.session.get('email')

    try:
        user = User.objects.get(email=email)
        users = User.objects.exclude(id=user.id)
    except User.DoesNotExist:
        request.session.flush()
        return redirect('login')

    return render(request, 'chat.html', {
        'user': user,
        'users': users
    })


@custom_login_required
def start_chat(request, user_id):
    other_user = get_object_or_404(User, id=user_id)

    current_user_id = request.session.get('user_id')
    if not current_user_id:
        return redirect('login')

    current_user = get_object_or_404(User, id=current_user_id)

    chat = Chat.objects.filter(
        (Q(user1=current_user) & Q(user2=other_user)) |
        (Q(user1=other_user) & Q(user2=current_user))
    ).first()

    messages = []
    if chat:
        messages = Message.objects.filter(chat=chat).order_by('created_at')

    context = {
        'other_user': other_user,
        'chat': chat,
        'messages': messages,
        'current_user': current_user
    }

    return render(request, 'chat/start_chat.html', context)


@require_POST
@csrf_exempt
def send_message(request):
    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({"status": "error", "message": "Invalid JSON"})

    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({"status": "error", "message": "Login required"})

    try:
        sender = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Sender not found"})

    receiver_id = data.get("receiver_id")
    message_text = data.get("content", "").strip()

    if not receiver_id or not message_text:
        return JsonResponse({"status": "error", "message": "Invalid data"})

    try:
        receiver = User.objects.get(id=receiver_id)
    except User.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Receiver not found"})

    Message.objects.create(
        sender=sender,
        receiver=receiver,
        text=message_text
    )

    return JsonResponse({"status": "success"})


def show_logs(request):
    import re
    from datetime import datetime

    logs_data = []
    log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs.txt')

    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = []

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Also pull real app events from Message model
    try:
        recent_messages = Message.objects.select_related('sender', 'receiver').order_by('-timestamp')[:30]
        for msg in recent_messages:
            logs_data.append({
                'time': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'level': 'INFO',
                'message': f'Message from {msg.sender.name} → {msg.receiver.name}: "{msg.text[:60]}"',
                'source': 'chat',
            })
    except Exception:
        pass

    # Parse raw log lines
    sql_pattern = re.compile(r'^\(([\d.]+)\)\s+(.+)$', re.DOTALL)
    file_pattern = re.compile(r'^File (.+) first seen')
    changed_pattern = re.compile(r'^(.+) changed, reloading')
    signal_pattern = re.compile(r'Signal results:')

    for line in reversed(lines[-300:]):
        line = line.strip()
        if not line:
            continue

        # Pipe-separated custom logs
        parts = line.split(' | ')
        if len(parts) == 3:
            logs_data.append({'time': parts[0], 'level': parts[1], 'message': parts[2], 'source': 'app'})
            continue

        # SQL queries
        m = sql_pattern.match(line)
        if m and ('SELECT' in line or 'INSERT' in line or 'UPDATE' in line or 'DELETE' in line):
            sql_preview = m.group(2).replace('\n', ' ').strip()[:120]
            logs_data.append({'time': now, 'level': 'DEBUG', 'message': f'SQL ({m.group(1)}s): {sql_preview}', 'source': 'sql'})
            continue

        # File changed / reload
        m = changed_pattern.search(line)
        if m:
            logs_data.append({'time': now, 'level': 'WARNING', 'message': f'Reload triggered: {m.group(1).split("/")[-1].split(chr(92))[-1]}', 'source': 'server'})
            continue

        # Server startup / key events
        if any(kw in line for kw in ['Watching for file changes', 'Apps ready', 'autoreload_started', 'Performing system checks']):
            logs_data.append({'time': now, 'level': 'INFO', 'message': line[:120], 'source': 'server'})
            continue

        # Skip noisy file-watch lines
        if file_pattern.match(line) or signal_pattern.search(line):
            continue

        # Catch-all for short meaningful lines
        if 10 < len(line) < 200 and not line.startswith('File '):
            level = 'ERROR' if 'error' in line.lower() or 'exception' in line.lower() or 'traceback' in line.lower() else \
                    'WARNING' if 'warn' in line.lower() or 'changed' in line.lower() else 'INFO'
            logs_data.append({'time': now, 'level': level, 'message': line[:150], 'source': 'server'})

    # Deduplicate and limit
    seen = set()
    unique_logs = []
    for log in logs_data:
        key = log['message'][:80]
        if key not in seen:
            seen.add(key)
            unique_logs.append(log)
        if len(unique_logs) >= 80:
            break

    return render(request, 'logs.html', {'logs': unique_logs})




@custom_login_required
def get_messages(request, user_id):
    current_user_id = request.session.get('user_id')

    # ❌ No user → return empty
    if not current_user_id:
        return JsonResponse({"messages": []})

    # ✅ 1. Mark messages as read (IMPORTANT 🔥)
    Message.objects.filter(
        sender_id=user_id,
        receiver_id=current_user_id,
        is_read=False
    ).update(is_read=True)

    # ✅ 2. Fetch chat messages
    messages = Message.objects.filter(
        Q(sender_id=current_user_id, receiver_id=user_id) |
        Q(sender_id=user_id, receiver_id=current_user_id)
    ).order_by('timestamp')

    # ✅ 3. Format response
    data = [
        {
            "id": msg.id,
            "sender": msg.sender_id,
            "message": msg.text,
            "time": msg.timestamp.strftime("%H:%M"),
            "is_read": msg.is_read
        }
        for msg in messages
    ]

    return JsonResponse({"messages": data})



def get_users_with_unread(request):
    current_user_id = request.session.get('user_id')
    if not current_user_id:
        return JsonResponse({"users": []})

    users = User.objects.exclude(id=current_user_id)
    user_list = []

    for u in users:
        unread_count = Message.objects.filter(
            sender=u,
            receiver_id=current_user_id,
            is_read=False
        ).count()
        user_list.append({"id": u.id, "unread": unread_count})

    return JsonResponse({"users": user_list})


# Simple in-memory typing store (good enough for single-server dev)
_typing_store = {}

@csrf_exempt
def set_typing(request):
    if request.method != 'POST':
        return JsonResponse({"status": "error"})
    current_user_id = request.session.get('user_id')
    if not current_user_id:
        return JsonResponse({"status": "error"})
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"status": "error"})
    receiver_id = str(data.get('receiver_id', ''))
    is_typing = bool(data.get('is_typing', False))
    key = f"{current_user_id}_{receiver_id}"
    import time
    _typing_store[key] = time.time() if is_typing else 0
    return JsonResponse({"status": "ok"})


def get_typing(request, user_id):
    current_user_id = request.session.get('user_id')
    if not current_user_id:
        return JsonResponse({"typing": False})
    import time
    key = f"{user_id}_{current_user_id}"
    last = _typing_store.get(key, 0)
    typing = (time.time() - last) < 3
    return JsonResponse({"typing": typing})


@custom_login_required
def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')


@custom_login_required
def admin_stats(request):
    total_users = User.objects.count()
    total_messages = Message.objects.count()
    from django.utils import timezone
    from datetime import timedelta
    recent_activity = Message.objects.filter(
        timestamp__gte=timezone.now() - timedelta(hours=24)
    ).count()
    return JsonResponse({
        'total_users': total_users,
        'total_messages': total_messages,
        'recent_activity': recent_activity
    })


@custom_login_required
def admin_logs(request):
    import re
    from datetime import datetime

    logs_data = []
    log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs.txt')

    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = []

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        recent_messages = Message.objects.select_related('sender', 'receiver').order_by('-timestamp')[:50]
        for msg in recent_messages:
            logs_data.append({
                'time': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'level': 'INFO',
                'message': f'Message from {msg.sender.name} → {msg.receiver.name}: "{msg.text[:60]}"',
                'source': 'chat',
            })
    except Exception:
        pass

    sql_pattern = re.compile(r'^\\(([\\d.]+)\\)\\s+(.+)$', re.DOTALL)
    changed_pattern = re.compile(r'^(.+) changed, reloading')

    for line in reversed(lines[-300:]):
        line = line.strip()
        if not line:
            continue

        parts = line.split(' | ')
        if len(parts) == 3:
            logs_data.append({'time': parts[0], 'level': parts[1], 'message': parts[2], 'source': 'app'})
            continue

        m = sql_pattern.match(line)
        if m and ('SELECT' in line or 'INSERT' in line or 'UPDATE' in line or 'DELETE' in line):
            sql_preview = m.group(2).replace('\\n', ' ').strip()[:120]
            logs_data.append({'time': now, 'level': 'DEBUG', 'message': f'SQL ({m.group(1)}s): {sql_preview}', 'source': 'sql'})
            continue

        m = changed_pattern.search(line)
        if m:
            logs_data.append({'time': now, 'level': 'WARNING', 'message': f'Reload triggered: {m.group(1).split("/")[-1].split(chr(92))[-1]}', 'source': 'server'})
            continue

        if any(kw in line for kw in ['Watching for file changes', 'Apps ready', 'autoreload_started', 'Performing system checks']):
            logs_data.append({'time': now, 'level': 'INFO', 'message': line[:120], 'source': 'server'})
            continue

        if 10 < len(line) < 200 and not line.startswith('File '):
            level = 'ERROR' if 'error' in line.lower() or 'exception' in line.lower() or 'traceback' in line.lower() else 'WARNING' if 'warn' in line.lower() or 'changed' in line.lower() else 'INFO'
            logs_data.append({'time': now, 'level': level, 'message': line[:150], 'source': 'server'})

    seen = set()
    unique_logs = []
    for log in logs_data:
        key = log['message'][:80]
        if key not in seen:
            seen.add(key)
            unique_logs.append(log)
        if len(unique_logs) >= 100:
            break

    return JsonResponse({'logs': unique_logs})
