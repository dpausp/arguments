from ekklesia_common import md
from morepath import redirect
from webob.exc import HTTPBadRequest

from ekklesia_portal.app import App
from ekklesia_portal.datamodel import Department, VotingPhase, VotingPhaseType
from ekklesia_portal.enums import VotingStatus
from ekklesia_portal.permission import CreatePermission, EditPermission

from .voting_phase_cells import EditVotingPhaseCell, NewVotingPhaseCell, VotingPhaseCell, VotingPhasesCell
from .voting_phase_contracts import VotingPhaseForm
from .voting_phases import VotingPhases


@App.permission_rule(model=VotingPhases, permission=CreatePermission)
def voting_phases_create_permission(identity, model, permission):
    if identity.has_global_admin_permissions:
        return True

    return identity.user.managed_departments


@App.permission_rule(model=VotingPhase, permission=EditPermission)
def voting_phase_edit_permission(identity, model, permission):
    if identity.has_global_admin_permissions:
        return True

    return model.department in identity.user.managed_departments


@App.path(model=VotingPhases, path='v')
def voting_phases():
    return VotingPhases()


@App.path(model=VotingPhase, path='v/{id}/{slug}', variables=lambda o: dict(id=o.id, slug=o.name or o.target or o.id))
def voting_phase_path(request, id, slug):
    return request.q(VotingPhase).get(id)


@App.html(model=VotingPhases)
def index(self, request):
    cell = VotingPhasesCell(self, request)
    return cell.show()


@App.html(model=VotingPhases, name='new', permission=CreatePermission)
def new(self, request):
    form = VotingPhaseForm(request, request.link(self))
    return NewVotingPhaseCell(request, form, form_data={}).show()


@App.html_form_post(model=VotingPhases, form=VotingPhaseForm, cell=NewVotingPhaseCell, permission=CreatePermission)
def create(self, request, appstruct):
    department_id = appstruct['department_id']


    if not request.identity.has_global_admin_permissions:
        department_allowed = [d for d in request.current_user.managed_departments if d.id == department_id]

        if not department_allowed:
            return HTTPBadRequest("department not allowed")

    voting_phase_type = request.q(VotingPhaseType).get(appstruct['phase_type_id'])

    if voting_phase_type is None:
        return HTTPBadRequest("voting phase type is missing")

    voting_phase = VotingPhase(**appstruct)
    request.db_session.add(voting_phase)
    request.db_session.flush()

    return redirect(request.link(voting_phase))


@App.html(model=VotingPhase, name='edit', permission=EditPermission)
def edit(self, request):
    form = VotingPhaseForm(request, request.link(self))
    return EditVotingPhaseCell(self, request, form).show()


@App.html_form_post(model=VotingPhase, form=VotingPhaseForm, cell=EditVotingPhaseCell, permission=EditPermission)
def update(self, request, appstruct):
    department_id = appstruct['department_id']

    if not request.identity.has_global_admin_permissions:
        department_allowed = [d for d in request.current_user.managed_departments if d.id == department_id]

        if not department_allowed:
            return HTTPBadRequest("department not allowed")

    voting_phase_type = request.q(VotingPhaseType).get(appstruct['phase_type_id'])

    if voting_phase_type is None:
        return HTTPBadRequest("voting phase type is missing")

    # after setting a target date, the state of the voting phase transitions to SCHEDULED
    if appstruct['target'] and self.target is None:
        appstruct['status'] = VotingStatus.SCHEDULED

    self.update(**appstruct)
    return redirect(request.link(self))


@App.html(model=VotingPhase)
def show(self, request):
    cell = VotingPhaseCell(self, request, show_edit_button=True, show_proposition_list=True, show_description=True)
    return cell.show()


@App.json(model=VotingPhase, name='spickerrr')
def spickerrr(self, request):
    propositions = [p for b in self.ballots for p in b.propositions]

    def serialize_proposition(proposition):
        proposition_type = proposition.ballot.proposition_type
        return {
            'url': request.link(proposition),
            'id': proposition.voting_identifier,
            'title': proposition.title,
            'type': proposition_type.name if proposition_type else None,
            'tags': ', '.join(t.name for t in proposition.tags),
            'text': md.convert(proposition.content),
            'remarks': md.convert(proposition.motivation)
        }

    return [serialize_proposition(p) for p in propositions]
