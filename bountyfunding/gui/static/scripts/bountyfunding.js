var slider = $('#ex1').slider({
    ticks: [0, 10, 20, 30, 40, 50],
    ticks_labels: ['€0', '€10', '€20', '€30', '€40', '€50'],
	tooltip: 'hide'
}).data('slider');

$("#ex1").on("slide", function(e) {
	$("#amount").val(e.value);
});

$("#amount").change(function(e) {
	var value = parseInt($("#amount").val());
	if (value > 50) {
		value = 50;
		$("#amount").val(value);
	}
	slider.setValue(value, false);
});

function validateNumber(e) {
	// Allow: backspace, delete, tab, escape, enter and .
	if ($.inArray(e.keyCode, [46, 8, 9, 27, 13, 110, 190]) !== -1 ||
		 // Allow: Ctrl+A
		(e.keyCode == 65 && e.ctrlKey === true) || 
		 // Allow: home, end, left, right
		(e.keyCode >= 35 && e.keyCode <= 39)) {
			 // let it happen, don't do anything
			 return;
	}
	// Ensure that it is a number and stop the keypress
	if ((e.shiftKey || (e.keyCode < 48 || e.keyCode > 57)) && (e.keyCode < 96 || e.keyCode > 105)) {
		e.preventDefault();
	}
}

$("#amount").keydown(validateNumber)

