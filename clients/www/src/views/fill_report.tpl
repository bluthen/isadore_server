<!DOCTYPE HTML>
<html>
<head>
<meta name="format-detection" content="telephone=no">
<link rel="stylesheet" type="text/css" href="../../../s/css/fill_report.css" media="screen" />
<link rel="stylesheet" type="text/css" href="../../../s/css/fill_report.css" media="print" />
<script type="text/javascript" src="../../../s/js/jquery-1.8.3.min.js"></script>
<script>
function resize(){
	$('.pages').height($(window).height() - 50);
}
$(document).ready(function() {
	resize();
	$('#print').click(function () {window.print();});
	$(window).resize(resize);
	$('#fill_select').change(function () {
		location.href="#fill"+$('#fill_select').val();
	});
	$('#images_checkbox').prop("checked", true);
	$('#images_checkbox').change(function ()  {
		if($('#images_checkbox').is(':checked')) {
			$('img').show();
			$('#spinner').show();
		} else {
			$('img').hide();
			$('#spinner').hide();
		}
	});
});
</script>
</head>
<body>
	<div class="navigation">
		<div class="navigation_wrapper">
			Go to fill#: <select id="fill_select">
%for fill in fills:
				<option value="{{!fill["fill_number"]}}">{{!fill["fill_number"]}}</option>
%end
			</select>
			<input id="images_checkbox" type="checkbox"><label for="images_checkbox"> Show Graphs</label>
			<span id="spinner">(Make sure all graphs are loaded before printing.)</span>
			<button id="print" type="button" name="print" value="print">Print</button>
		</div>
	</div>
	<div class="pages">
%for fill in fills:
		<div class="page">
			<a id="fill{{!fill["fill_number"]}}"></a>
			<div class="report_title">{{!report_title}}</div>
			<div class="top_section section">
				<div class="year_column">
					<div class="year_label">Year</div>
					<div class="year_value">{{!fill["year"]}}</div>
					<div class="year_label">Type</div>
%if fill['fill_type_id'] == '2':
					<div class="year_value">Bypass</div>
%else:
					<div class="year_value">Normal</div>
%end
				</div>
				<div class="fill_column">
					<div class="label_column">
						<div class="side_label">Fill Number:</div>
						<div class="side_label">Rotation:</div>
						<div class="side_label">Bin Number:</div>
						<div class="side_label">Lot Number:</div>
					</div>
					<div class="value_column">
						<div class="side_value">{{!fill["fill_number"]}}</div>
						<div class="side_value">{{!fill["rotation"]}}</div>
						<div class="side_value">{{!fill["bin_number"]}}</div>
						<div class="side_value">{{!fill["lot_number"]}}</div>
					</div>
				</div>
				<div class="hybrid_column">
						<div class="side_block_label"><span class="side_block_label">Hybrid:&nbsp;&nbsp;</span><div class="side_block_value">{{!fill["hybrid"]}}</div></div>
						<div class="side_block_label"><span class="side_block_label">Field:&nbsp;&nbsp;</span><div class="side_block_value">{{!fill["field_name"]}}</div></div>
						<div class="side_block_label"><span class="side_block_label">Truck:&nbsp;&nbsp;</span><div class="side_block_value">{{!fill["truck"]}}</div></div>
						<div class="side_block_label"><span class="side_block_label">Depth:&nbsp;&nbsp;</span><div class="side_block_value">{{!fill["depth"]}}</div></div>
				</div>
				<div class="wclears"></div>
			</div>
			<div class="air_section section">
				<div class="centered section_title">
					<span>Air Times</span>
				</div>
				<div class="time_column">
					<div class="label_column">
						<div class="side_label">Start Air Time:</div>
						<div class="side_label">Roll Time:</div>
						<div class="side_label">End Time:</div>
					</div>
					<div class="value_column">
						<div class="side_value">{{!fill["air_begin_time"]}}</div>
						<div class="side_value">{{!fill["roll_time"]}}</div>
						<div class="side_value">{{!fill["air_end_time"]}}</div>
					</div>
				</div>
				<div class="air_column">
					<div class="label_column">
						<div class="side_label">Up Air Time:</div>
						<div class="side_label">Down Air Time:</div>
						<div class="side_label">Total Air Time:</div>
					</div>
					<div class="value_column">
						<div class="side_value">{{!fill["up_time"]}} <span class="side_value_extra">{{!fill["up_percent"]}}%</span></div>
						<div class="side_value">{{!fill["down_time"]}} <span class="side_value_extra">{{!fill["down_percent"]}}%</span></div>
						<div class="side_value">{{!fill["air_total"]}}</div>
					</div>
				</div>
				<div class="wclears"></div>
			</div>
			<div class="mc_section section">
				<div class="centered">
					<div class="label_column">
						<div class="side_label">Ear H2O:</div>
					</div>
					<div class="value_column">
%if isinstance(fill["pre_mc"], list):
%for mc in fill["pre_mc"]:
						<div class="side_value">{{!mc}}</div>
%end
%else:
						<div class="side_value">{{!fill["pre_mc"]}}</div>
%end
					</div>
				</div>
				<div class="wclears"></div>
			</div>
			<div class="shelled_section section">
				<div class="centered section_title">
					<span>Shelled Data</span>
				</div>
				<div class="shelled_mc_column">
					<div class="label_column">
						<div class="side_label">% H2O:</div>
%if 'reports' in general['configs'] and 'avg_wetbulb' in general['configs']['reports'] and general['configs']['reports']['avg_wetbulb']:
						<div class="side_label">Avg Wetbulb:</div>
%end
					</div>
					<div class="value_column">
%if isinstance(fill["post_mc"], list):
%for mc in fill["post_mc"]:
						<div class="side_value">{{!mc}}&nbsp;</div>
%end
%else:
						<div class="side_value">{{!fill["post_mc"]}}&nbsp;</div>
%end
%if 'reports' in general['configs'] and 'avg_wetbulb' in general['configs']['reports'] and general['configs']['reports']['avg_wetbulb']:
						<div class="side_value">{{!fill["avg_wetbulb"]}}&nbsp;</div>
%end
					</div>
				</div>
				<div class="shelled_other_column">
					<div class="label_column">
						<div class="side_label">Average H2O:</div>
						<div class="side_label">Bushels in Bin:</div>
						<div class="side_label">Hrs/Pt:</div>
					</div>
					<div class="value_column">
						<div class="side_value">{{!fill["post_avg"]}}&nbsp;</div>
						<div class="side_value">{{!fill["bushels"]}}&nbsp;</div>
						<div class="side_value">{{!fill["hrs_per_point"]}}&nbsp;</div>
					</div>
				</div>
				<div class="clears centered">
					<div class="label_column">
						<div class="side_label">Storage Bin:</div>
					</div>
					<div class="value_column">
						<div class="side_value">{{!fill["storage_code"]}} {{!fill["storage_number"]}}</div>
					</div>
				</div>
				<div class="fill_img clears">
					<img src="../graphp?fill_id={{!fill["id"]}}&display_tz={{!display_tz}}&ts={{!ts}}" alt="Fill graph"/>
				</div>
				<div class="wclears"></div>
			</div>
		</div>
%end
	</div>
</body>
</html>
