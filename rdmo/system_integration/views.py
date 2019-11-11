from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
import json
import requests
import logging
from ..projects.models import Project

log = logging.getLogger(__name__)

mediator_url = 'http://localhost'
mediator_port = 8040
mediator_app_name = '/mediator'
mediator_systems = '/systems'
mediator_projects = '/projects'
mediator_projectdata = '/projectdata'


# Overview of all Systems that are registered in the mediator
class SystemsView(LoginRequiredMixin, TemplateView):
    template_name = 'system_integration/systems.html'
    error_template = 'system_integration/systems_error.html'
    def get(self, request, rdmo_project_id):
        # Try to get the information from the mediator.
        try:
            response = requests.get(mediator_url + ':' + str(mediator_port) + mediator_app_name + mediator_systems)
        except:
            log.info('Connection error. Getting external systems failed.')
            return render(request, self.error_template, status=400)

        # Try to parse the json response into a python data structure.
        try:
            json_response = response.json()
        except:
            log.info('Json parsing error. Getting external systems failed.')
            return render(request, self.error_template, status=400)
        return render(request, self.template_name, {'rdmo_project_id':rdmo_project_id, 'systems':json_response})


class LoginView(LoginRequiredMixin, TemplateView):
    template_name = 'system_integration/login.html'
    error_template = 'system_integration/systems_error.html'
    auth_error_template = 'system_integration/method_error.html'

    def get(self, request, rdmo_project_id, system_id):
        # Token already obtained, RDMO project and external system chosen:
        if 'devicedb_token_'+str(system_id) in request.session and rdmo_project_id and system_id:
            # Go directly to project overview of external system
            return redirect('/system_integration/projects/' + str(rdmo_project_id) + '/' +str(system_id))
        # no token but RDMO project and system chosen:
        elif rdmo_project_id and system_id:
            # Get information of external system from mediator, if necessary show login form
            try:# get system info
                r = requests.get(mediator_url + ':' + str(mediator_port) + mediator_app_name + mediator_systems + '/' + str(system_id))
            except:
                log.info('Connection error. Getting information of external system failed.')
                return render(request, self.error_template, status=400)

            # Try to parse the json response into a python data structure.
            try:
                json_response = r.json()
            except:
                log.info('Json parsing error. Getting information of external system failed.')
                return render(request, self.error_template, status=400)

            # show login form in case of password authentication
            if json_response['grant_type'] == 'password':
                return render(request, 'system_integration/login.html', {'rdmo_project_id':rdmo_project_id, 'system_name':json_response['name'], 'system_id':system_id})
            # if there is no authentication go directly to project overview of external system
            elif json_response['grant_type'] == '':
                return redirect('/system_integration/projects/' + str(rdmo_project_id) + '/' +str(system_id))
            else:
                log.info('Unsupported authentication method.')
                return render(request, self.auth_error_template, status=400)
        # no external system chosen: Go to system overview
        elif rdmo_project_id:
            return redirect('/system_integration/login/' + str(rdmo_project_id))
        # no RDMO project chosen: Go to RDMO project overview
        else:
            return redirect('/projects')

    def post(self, request, *args, **kwargs):
        # Try to get the information from the mediator.
        try:
            r = requests.get(mediator_url + ':' + str(mediator_port) + mediator_app_name + mediator_systems + '/' + request.POST.get('system_id',''))
        except:
            log.info('Connection error. Getting information of external system failed.')
            return render(request, self.error_template, status=400)

        # Try to parse the json response into a python data structure.
        try:
            json_response = r.json()
        except:
            log.info('Json parsing error. Getting information of external system failed.')
            return render(request, self.error_template, status=400)

        if 'grant_type' in json_response.keys():
            if json_response['grant_type'] == 'password':
                data = {'grant_type':json_response['grant_type'], 
                        'username':request.POST.get('username',''), 
                        'password':request.POST.get('password','')}

                try:
                    r = requests.post(json_response['auth_url'], data=data, auth=(json_response['app_name'],json_response['app_secret']))
                except:
                    log.info('Connection error. Login at external system failed.')
                    return render(request, self.error_template, status=400)

                try:
                    json_response_ext_system = r.json()
                except:
                    log.info('Json parsing error. Login at external system failed.')
                    return render(request, self.error_template, status=400)

                if 'access_token' in json_response_ext_system.keys():
                    request.session['devicedb_token_'+request.POST.get('system_id','')] = json_response_ext_system['access_token']
                    return redirect('/system_integration/login/' + request.POST.get('rdmo_project_id','') + '/'+request.POST.get('system_id',''))
                else:
                    error_message = ''
                    if 'error' in json_response_ext_system.keys():
                        error_message = json_response_ext_system['error']

                    return render(request, 'system_integration/login.html', {'rdmo_project_id':request.POST.get('rdmo_project_id',''), 'system_name':json_response['name'], 'system_id':request.POST.get('system_id',''), 'error_message':error_message})
            else:
                log.info('Unsupported authentication method.')
                return render(request, self.auth_error_template, status=400)
        else:
            log.info('Invalid response from mediator.')
            return render(request, self.auth_error_template, status=400)


class ProjectOverviewView(LoginRequiredMixin, TemplateView):
    template_name = 'system_integration/login.html'
    error_template = 'system_integration/systems_error.html'

    def get(self, request, rdmo_project_id, system_id):
        # Token obtained, RDMO project and external system chosen:
        if 'devicedb_token_' + str(system_id) in request.session and rdmo_project_id and system_id:
            # send request for project list
            token = request.session['devicedb_token_' + str(system_id)]
            link = mediator_url + ':' + str(mediator_port) + mediator_app_name + mediator_projects + '/'
            try:
                r = requests.get(link, params = {'devicedb_token':token, 'sys_id':system_id})
            except:
                log.info('Connection error. Getting projects from external system failed.')
                return render(request, self.error_template, status=400)
            try:
                json_response = r.json()
            except:
                log.info('Json parsing error. Getting information of external system failed.')
                return render(request, self.error_template, status=400)

            return render(request, 'system_integration/projects.html', {'projects':json_response, 'rdmo_project_id':rdmo_project_id, 'system_id':system_id})
        # no token but RDMO project and system chosen:
        elif rdmo_project_id and system_id:
            # Get information of external system, if necessary show login form
            return redirect('/system_integration/login/' + str(rdmo_project_id) + '/' + str(system_id))
        # no external system chosen:
        elif rdmo_project_id:
            # Go to system overview
            return redirect('/system_integration/login/'+str(rdmo_project_id))
        # no RDMO project chosen:
        else:
            # Go to RDMO project overview
            return redirect('/projects/')


class ImportProjectdataView(LoginRequiredMixin, TemplateView):
    model = Project
    permission_required = 'projects.change_project_object'

    template_name = 'system_integration/login.html'
    error_template = 'system_integration/systems_error.html'

    def post(self, request, *args, **kwargs):
        if 'devicedb_token_'+str(request.POST.get('system_id','')) in request.session and request.POST.get('system_id', ''):
            token = request.session['devicedb_token_'+str(request.POST.get('system_id',''))]
            link = mediator_url + ':' + str(mediator_port) + mediator_app_name + mediator_projects + '/'
            try:
                r = requests.get(link, params = {'devicedb_token':token, 'sys_id':request.POST.get('system_id','')})
            except:
                log.info('Connection error. Getting projects from external system failed.')
                return render(request, self.error_template, status=400)
            try:
                json_response = r.json()
            except:
                log.info('Json parsing error. Getting information of external system failed.')
                return render(request, self.error_template, status=400)

            projects = []
            for project in json_response['projects']:
                if str(request.POST.get('project_'+str(project['id']), '0')) == '1':
                    projects += [project['id']]
            if projects:
                # send request to mediator
                # The mediator gets a list with the project IDs and the ID of the external system and passes the request to the external system.
                # The response of the external system is sent back to the mediator, then processed by the mediator and then the processed data is sent back to the rdmo.
                projects_json = json.dumps(projects)
                link = mediator_url + ':' + str(mediator_port) + mediator_app_name + mediator_projectdata + '/'
                try:
                    r = requests.get(link, params = {'devicedb_token':token, 'sys_id':request.POST.get('system_id',''), 'projects':projects_json})
                except:
                    log.info('Connection error. Getting project data from external system failed.')
                    return render(request, self.error_template, status=400)
                try:
                    json_response = r.json()
                except:
                    log.info('Json parsing error. Getting project data of external system failed.')
                    return render(request, self.error_template, status=400)

                # !!! import should start here !!!
                # !!! at first be sure you made some snapshots !!!
                return HttpResponse('Data requested for projects (IDs): '+projects_json+'</br>Data: '+str(json_response))
            else:
                return redirect('/system_integration/projects/' + request.POST.get('rdmo_project_id','') + '/' + request.POST.get('system_id',''))
