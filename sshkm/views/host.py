from django.conf import settings
from django.utils import timezone
from django.utils.formats import localize
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, JsonResponse
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist

from sshkm.tasks import ScheduleDeployKeys
from sshkm.views.deploy import DeployKeys, DeployConfig, NothingToDeployException

from sshkm.models import Host, Setting, Permission
from sshkm.forms import HostForm
from taskqueue.executor import ExecutorConnection


@login_required
def HostList(request):
    hosts = Host.objects.order_by('name')

    # if hosts are created check if public/private keys are uploaded to make deployment possible
    keys = Setting.objects.filter(name__in=['MasterKeyPrivate', 'MasterKeyPublic']).count()
    if hosts and keys != 2:
        messages.add_message(request, messages.WARNING, "To be able to deploy keys to your hosts please navigate to the settings page and upload your master private and public key (as user with Admin priviledges).")

    context = {
                'hosts': hosts,
                'STATE_SUCCESS': DeployConfig.STATE_SUCCESS, 
                'STATE_PENDING': DeployConfig.STATE_PENDING, 
                'STATE_FAILURE': DeployConfig.STATE_FAILURE, 
                'STATE_NOTHING_TO_DEPLOY': DeployConfig.STATE_NOTHING_TO_DEPLOY
              }

    return render(request, 'sshkm/host/list.html', context)

@login_required
def HostState(request):
    ids = request.POST.getlist('id', request.GET.getlist('id'))
    data = []
    
    if len(ids) > 0:
        hosts = Host.objects.filter(id__in=ids)

        for host in hosts:
            data.append(host.toJson())

    return JsonResponse(data, safe=False)

@login_required
def HostDetail(request):
    if request.method == 'GET' and 'id' in request.GET:
        host = get_object_or_404(Host, pk=request.GET['id'])
        hostform = HostForm(instance=host)
        permissions = Permission.objects.filter(host_id=request.GET['id'])
        return render(request, 'sshkm/host/detail.html', {
            'hostform': hostform,
            'permissions': permissions,
        })
    else:
        hostform = HostForm()
        return render(request, 'sshkm/host/detail.html', {
            'hostform': hostform,
        })

@login_required
def HostDelete(request):
    try:
        if request.POST.get('id_multiple') is not None:
            Host.objects.filter(id__in=request.POST.getlist('id_multiple')).delete()
            messages.add_message(request, messages.SUCCESS, "Hosts deleted")
        else:
            host = Host.objects.get(id=request.GET['id'])
            delete = Host(id=request.GET['id']).delete()
            messages.add_message(request, messages.SUCCESS, "Host " + host.name + " deleted")
    except ObjectDoesNotExist as e:
        messages.add_message(request, messages.ERROR, "The host could not be deleted")
    except Exception as e:
        messages.add_message(request, messages.ERROR, "The host could not be deleted")

    return HttpResponseRedirect(reverse('HostList'))

@login_required
def HostSave(request):
    try:
        if request.POST.get('id') is not None:
            hostInstance = Host.objects.get(id=request.POST.get('id'))
            host = HostForm(request.POST, instance=hostInstance)
        else:
            host = HostForm(request.POST)
        host.save()
        messages.add_message(request, messages.SUCCESS, "Host " + request.POST.get('name') + " sucessfully saved")
    except IntegrityError as e:
        messages.add_message(request, messages.ERROR, "The host could not be saved. "+str(e))
    except Exception as e:
        messages.add_message(request, messages.ERROR, "The host could not be saved. "+str(e))

    return HttpResponseRedirect(reverse('HostList'))

@login_required
def HostDeploy(request):
    if settings.SSHKM_DEMO is False:
        try:
            deployConfig = DeployConfig()

            if request.POST.get('id_multiple') is not None:
                pw=b'g3t1o5t' #:TODO should be in a config file
                con = ExecutorConnection('127.0.0.1', 50000, pw)
                idList = request.POST.getlist('id_multiple')
                Host.objects.filter(id__in=idList).update(status=DeployConfig.STATE_PENDING) # set status of hosts to deploy to PENDING

                for host in request.POST.getlist('id_multiple'):
                    con.call_async(DeployKeys, host, deployConfig)

                messages.add_message(request, messages.INFO, "Multiple host deployment initiated")
            else:
                host = Host.objects.get(id=request.GET['id'])
                try:
                    deploy = DeployKeys(request.GET['id'], deployConfig)
                    messages.add_message(request, messages.SUCCESS, "Host " + host.name + " deployed")
                except NothingToDeployException as e:
                    messages.add_message(request, messages.INFO, "Nothing to deploy for Host " + host.name)
                except Exception as e:
                    messages.add_message(request, messages.ERROR, "Host " + host.name + " could not be deployed "+str(e))
        except ConnectionRefusedError as e:
            messages.add_message(request, messages.ERROR, "The host(s) could not be deployed. Remote taskqueue is not running.")
        except Exception as e:
            messages.add_message(request, messages.ERROR, "The host(s) could not be deployed: "+str(e))
    else:
        messages.add_message(request, messages.INFO, "Deployment is disabled in demo mode.")

    return HttpResponseRedirect(reverse('HostList'))
