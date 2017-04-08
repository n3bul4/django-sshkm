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

#from sshkm.tasks import ScheduleDeployKeys
from sshkm.views.deploy import DeployKeys, DeployConfig, NothingToDeployException

from sshkm.models import Host, Setting, Permission
from sshkm.forms import HostForm
from sshkm.tasks import RemoteTaskQueueProvider, CeleryProvider
from kombu.exceptions import OperationalError

@login_required
def HostList(request):
    hosts = Host.objects.order_by('name')

    # if hosts are created check if public/private keys are uploaded to make deployment possible
    keys = Setting.objects.filter(name__in=['MasterKeyPrivate', 'MasterKeyPublic']).count()
    if hosts and keys != 2:
        messages.add_message(request, messages.WARNING, "To be able to deploy keys to your hosts please navigate to the settings page and upload your master private and public key (as user with Admin priviledges).")

    context = {
                'hosts': hosts,
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
        idList = request.POST.getlist('id', request.GET.getlist("id"))
        idListLength = len(idList)

        if idListLength > 1:
            Host.objects.filter(id__in=idList).delete()
            messages.add_message(request, messages.SUCCESS, "Hosts deleted")
        elif idListLength == 1:
            host = Host.objects.get(id=idList[0])
            host.delete()
            messages.add_message(request, messages.SUCCESS, "Host " + host.name + " deleted")
        else:
            messages.add_message(request, messages.SUCCESS, "Did not receive any GET or POST id(s) to delete")
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
        deployConfig = DeployConfig()
        idList = request.POST.getlist('id', request.GET.getlist("id"))
        idListLength = len(idList)

        if idListLength > 1:
            hosts = Host.objects.filter(id__in=idList)

            try:
                taskProvider = RemoteTaskQueueProvider("127.0.0.1", 50000, pw=b'g3t1o5t')
                #taskProvider = CeleryProvider()
                hosts.update(status=Host.STATE_PENDING) # set status of hosts to deploy to PENDING

                for host in hosts:
                    taskProvider.call_async(host, deployConfig)

                messages.add_message(request, messages.INFO, "Multiple host deployment initiated")
            except (ConnectionRefusedError, OperationalError) as e: # OperationalError = Recoverable message transport connection error due to celery api
                errorMsg = "The host(s) could not be deployed. "+taskProvider.getName()+" is not running."
                hosts.update(status=Host.STATE_FAILURE, error_msg=errorMsg)
                messages.add_message(request, messages.ERROR, errorMsg)
            except Exception as e:
                errorMsg = "The host(s) could not be deployed: "+str(e)+" "+str(e.__class__)
                hosts.update(status=Host.STATE_FAILURE, error_msg=errorMsg)
                messages.add_message(request, messages.ERROR, errorMsg)
        elif idListLength == 1:
            host = Host.objects.get(id=idList[0])

            try:
                DeployKeys(host, deployConfig)
                messages.add_message(request, messages.SUCCESS, "Host " + host.name + " deployed")
            except NothingToDeployException as e:
                messages.add_message(request, messages.INFO, "Nothing to deploy for Host " + host.name)
            except Exception as e:
                messages.add_message(request, messages.ERROR, "Host " + host.name + " could not be deployed "+str(e))
        else:
             messages.add_message(request, messages.ERROR, "Did not receive any GET or POST id(s) to deploy")
    else:
        messages.add_message(request, messages.INFO, "Deployment is disabled in demo mode.")

    return HttpResponseRedirect(reverse('HostList'))
