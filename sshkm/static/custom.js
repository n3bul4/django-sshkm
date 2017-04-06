// select all functionality
$(".checkAll").click(function () {
  $(this).closest('form').find(':checkbox').prop('checked', $(this).prop('checked'));
});


// dialogs
function checkboxCheck(action, element, title_confirm, message_confirm, title_noselect, message_noselect) {
  var checkboxs=document.getElementsByName(element);
  var okay=false;

  for(var i=0,l=checkboxs.length;i<l;i++) {
    if(checkboxs[i].checked) {
      okay=true;
      break;
    }
  }

  if(okay) {
    BootstrapDialog.confirm(
      {
        title: title_confirm,
        message: message_confirm,
        btnOKClass: 'btn-default',
        callback: function(result) {
          if(result) {
            action();
          }
        }
      }
    );
  } else {
    BootstrapDialog.alert(
      {
        title: title_noselect,
        message: message_noselect,
        btnOKClass: 'btn-default'
      }
    );
  }
}


// two-side multiselect
$("#btnLeft").click(function () {
  var selectedItem = $("#rightValues option:selected");
  $("#leftValues").append(selectedItem);
});

$("#btnRight").click(function () {
  var selectedItem = $("#leftValues option:selected");
  $("#rightValues").append(selectedItem);
});

function selectAll(box) { 
  selectBox = document.getElementById(box);

  for (var i = 0; i < selectBox.options.length; i++) { 
    selectBox.options[i].selected = true; 
  } 
}


// DataTable
$(document).ready(function(){
  var dataTable = $('.DataTable').DataTable({
    paging: false,
    info: false
  });

  $("#searchbox").on("keyup search input paste cut", function() {
    dataTable.search(this.value).draw();
  });
});

/*
var oTable;
$(document).ready(function(){
  oTable = $(".DataTablePermissions").dataTable({
    info: false,
    "pageLength": 50
  });

  function refreshCurrentPage() {
    var table = $('.DataTablePermissions').DataTable();
    var info = table.page.info();
    $(".tableInfo").text((info.page+1)+' of '+info.pages);
  }

  $(".paginate_left").click(function(){
    oTable.fnPageChange( 'previous' );
    refreshCurrentPage();
  });

  $(".paginate_right").click(function(){
    oTable.fnPageChange( 'next' );
    refreshCurrentPage();
  });

  $(oTable.on('search.dt', function(){
    refreshCurrentPage();
  }));

  $(oTable.off('search.dt', function(){
    refreshCurrentPage();
  }));

  refreshCurrentPage();
});
*/


// monitor deployment
$(document).ready(
  function(){
    var ids = {};

    $('.monitor_state').each(
      function(){
        var host_id = this.id.replace(/host/, '');
        ids[host_id] = host_id;
      }
    );

    keys = Object.keys(ids);

    if(keys.length > 0){
        var intervalId = setInterval(
        function(){
          queryString = "";

          for(i=0; i<keys.length; i++)
            queryString += "id="+keys[i]+"&";

          queryString += 'csrfmiddlewaretoken='+$("input[name='csrfmiddlewaretoken']").val()

          $.ajax(
            {
              type: "POST",
              url: '/host/state/',
              dataType : 'json',
              data: queryString,
              cache: false,
              success: function(respData) {
                var iconclass;

                for(i=0; i<respData.length; i++) {                  
                  switch(respData[i].status) {
                    case 'SUCCESS':
                      iconclass = 'glyphicon glyphicon-ok';
                      break;
                    case 'FAILURE':
                      iconclass = 'glyphicon glyphicon-remove';
                      break;
                    case 'PENDING':
                      iconclass = 'glyphicon glyphicon-refresh monitor_state';
                      break;
                    case 'NOTHING TO DEPLOY':
                      iconclass = 'glyphicon glyphicon-option-horizontal';
                      break;
                    default:
                      iconclass = '';
                  }

                  if(respData[i].status != 'PENDING'){
                    delete ids[respData[i].id];
                  }

                  $('#host'+respData[i].id).removeClass();
                  $('#host'+respData[i].id).addClass(iconclass);
                  $('span#host'+respData[i].id).attr('title', respData[i].status+' '+respData[i].last_status);
                }

                keys = Object.keys(ids);

                if(keys.length <= 0){
                  clearInterval(intervalId);
                }       
              },
              error: function(xhr, statusText, err){
                clearInterval(intervalId);
                alert("An error occurred while trying to get deployment status: " + xhr.status + " " + err);
              }
            }
          );
        },
        2000
      );
    }
  }
);