$(function() {

$("#confirm-button").click(function() {
	$("#confirm-button").hide()
	$("#confirm-options").show()
})

$("#confirm-cancel").click(function() {
	$("#confirm-options").hide()
	$("#confirm-button").show()
})

$("#confirm-options").hide()

});

