import json


from django.conf import settings
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


from judge import event_poster as event
from judge.models import Profile
from judge.models.submission import Submission
from judge.virtual_judge_utils import unpack


@csrf_exempt
def update_submission(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    data = json.loads(request.body)
    data = unpack(data, settings.VIRTUAL_JUDGE_KEY)
    data = json.loads(data)

    if not data:
        return JsonResponse({'error': 'Lmao'}, status=403)

    submission_id = data['submission_id']

    try:
        verdict = data['verdict']
        time = data['time']
        memory = data['memory']
    except BaseException:
        verdict = 'IE'
        time = 0
        memory = 0

    updates = {
        'time': time,
        'memory': memory,
        'points': 1 if verdict == 'AC' else 0,
        'result': verdict,
        'status': 'D' if (verdict != 'IE' and verdict != 'CE') else verdict,
        'case_total': 1,
        'case_points': 1 if verdict == 'AC' else 0,
        'current_testcase': 1,
        'is_virtual_judged': True,
    }

    submission = Submission.objects.filter(id=submission_id).update(**updates)
    submission = Submission.objects.filter(id=submission_id).first()

    event.post(
        'submissions',
        {
            'type': 'done-submission',
            'state': 'D',
            'id': submission_id,
            'contest': submission.contest_object_id,
            'user': submission.user_id,
            'problem': submission.problem_id,
            'status': submission.status,
            'language': submission.language_id,
            'organizations': [
                x[0]
                for x in Profile.objects.get(
                    id=submission.user_id,
                ).organizations.values_list('id')
            ],
        },
    )

    event.post(
        'sub_%s' % submission.id_secret,
        {
            'type': 'grading-end',
            'time': time,
            'memory': memory,
            'points': (1 if verdict == 'AC' else 0) * float(submission.problem.points),
            'total': float(submission.problem.points),
            'result': submission.result,
        },
    )

    return HttpResponse(status=200)
