from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db.models import Max, OuterRef, Subquery
from django.template.defaultfilters import floatformat
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _, gettext_lazy, ungettext

from judge.contest_format.default import DefaultContestFormat
from judge.contest_format.registry import register_contest_format
from judge.utils.timedelta import nice_repr


@register_contest_format('thtc1')
class THTC1ContestFormat(DefaultContestFormat):
    """
    All logic are the same as old VNOJ format, except that it will get the last submission instead of the highest score.
    """

    name = gettext_lazy('THT C1')
    config_defaults = {'penalty': 5, 'LSO': False}
    config_validators = {'penalty': lambda x: x >= 0, 'LSO': lambda x: isinstance(x, bool)}
    """
        penalty: Number of penalty minutes each incorrect submission adds. Defaults to 5.
        LSO: Last submission only. If true, cumtime will used the last submission time, not the total time of
        all submissions.
    """

    @classmethod
    def validate(cls, config):
        if config is None:
            return

        if not isinstance(config, dict):
            raise ValidationError('THT C1-styled contest expects no config or dict as config')

        for key, value in config.items():
            if key not in cls.config_defaults:
                raise ValidationError('unknown config key "%s"' % key)
            if not isinstance(value, type(cls.config_defaults[key])):
                raise ValidationError('invalid type for config key "%s"' % key)
            if not cls.config_validators[key](value):
                raise ValidationError('invalid value "%s" for config key "%s"' % (value, key))

    def __init__(self, contest, config):
        self.config = self.config_defaults.copy()
        self.config.update(config or {})
        self.contest = contest

    def update_participation(self, participation):
        cumtime = 0
        last = 0
        penalty = 0
        score = 0
        format_data = {}

        submissions = participation.submissions.exclude(submission__result__in=('IE', 'CE'))

        # select latest submission for each problem, from ecoo format
        queryset = (
            submissions
            .values('problem_id')
            .filter(
                submission__date=Subquery(
                    submissions
                    .filter(problem_id=OuterRef('problem_id'))
                    .order_by('-submission__date')
                    .values('submission__date')[:1],
                ),
            )
            .annotate(points=Max('points'))
            .values_list('problem_id', 'points', 'submission__date')
        )

        for prob, points, time in queryset:
            dt = (time - participation.start).total_seconds()

            # Compute penalty
            if self.config['penalty']:
                # An IE can have a submission result of `None`
                subs = participation.submissions.exclude(submission__result__isnull=True) \
                                                .exclude(submission__result__in=['IE', 'CE']) \
                                                .filter(problem_id=prob)

                if points:
                    prev = subs.filter(submission__date__lt=time).count()
                    penalty += prev * self.config['penalty'] * 60
                else:
                    # We should always display the penalty, even if the user has a score of 0
                    prev = subs.count()
            else:
                prev = 0

            if points:
                cumtime += dt
                last = max(last, dt)

            format_data[str(prob)] = {'time': dt, 'points': points, 'penalty': prev}
            score += points

        participation.cumtime = (last if self.config['LSO'] else cumtime) + penalty
        participation.score = round(score, self.contest.points_precision)
        participation.tiebreaker = last  # field is sorted from least to greatest
        participation.format_data = format_data
        participation.save()

    def display_user_problem(self, participation, contest_problem, frozen=False):
        format_data = (participation.format_data or {}).get(str(contest_problem.id))
        if format_data:
            penalty = format_html('<small style="color:red"> ({penalty})</small>',
                                  penalty=floatformat(format_data['penalty'])) if format_data['penalty'] else ''
            return format_html(
                '<td class="{state}"><a href="{url}">{points}{penalty}<div class="solving-time">{time}</div></a></td>',
                state=(('pretest-' if self.contest.run_pretests_only and contest_problem.is_pretested else '') +
                       self.best_solution_state(format_data['points'], contest_problem.points)),
                url=reverse('contest_user_submissions',
                            args=[self.contest.key, participation.user.user.username, contest_problem.problem.code]),
                points=floatformat(format_data['points'], -self.contest.points_precision),
                penalty=penalty,
                time=nice_repr(timedelta(seconds=format_data['time']), 'noday'),
            )
        else:
            return mark_safe('<td></td>')

    def get_short_form_display(self):
        yield _('The score on your **last** non-CE submission for each problem will be used.')

        penalty = self.config['penalty']
        if penalty:
            yield ungettext(
                'Each submission before the last submission will incur a **penalty of %d minute**.',
                'Each submission before the last submission will incur a **penalty of %d minutes**.',
                penalty,
            ) % penalty
            if self.config['LSO']:
                yield _('Ties will be broken by the time of the last submission (including penalty).')
            else:
                yield _('Ties will be broken by the sum of the last submission time on problems with '
                        'a non-zero score (including penalty), followed by the time of the last submission.')
        else:
            if self.config['LSO']:
                yield _('Ties will be broken by the time of the last submission.')
            else:
                yield _('Ties will be broken by the sum of the last submission time on problems with '
                        'a non-zero score, followed by the time of the last submission.')
