//   Copyright 2010-2019 Dan Elliott, Russell Valentine
//
//   Licensed under the Apache License, Version 2.0 (the "License");
//   you may not use this file except in compliance with the License.
//   You may obtain a copy of the License at
//
//       http://www.apache.org/licenses/LICENSE-2.0
//
//   Unless required by applicable law or agreed to in writing, software
//   distributed under the License is distributed on an "AS IS" BASIS,
//   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//   See the License for the specific language governing permissions and
//   limitations under the License.

function BinLightbox() {
	var self=this;
	var currentBin = null;
	var tabs = null;
	var dialog = null;
	this.tabHandlers=[];
	var init = function(){
		$('#bin_lightbox_next').click(function () {
			$('#bin_lightbox_fadewrapper').fadeOut('slow', function() {
				if(currentBin) {
					var nextBin = getNextBin(currentBin);
					self.open(nextBin.id, nextBin);
				}
			});
		});
		$('#bin_lightbox_previous').click(function() {
			$('#bin_lightbox_fadewrapper').fadeOut('fast', function() {
				if(currentBin) {
					var previousBin = getPreviousBin(currentBin);
					self.open(previousBin.id, previousBin);
				}
			});
		});
		self.tabHandlers=[new GraphsTabCustom(), new GraphTab(self), new ControlTab(), new FillTab(), new SetupTab()];
		tabs = $('#bin_lightbox_tabs').tabs({show: updateTab});
		dialog = new IsadoreDialog($('#bin_lightbox'), {width: 995,	open: updateTab});
	};

    /**
     * Gets next bin by position.
     *
     * @param bin
     *            The current bin where you want he bin tot he right of this
     *            one.
     */
    var getNextBin = function (bin) {
        var ii;
        for (ii = 0; ii < IsadoreData.bins.length; ++ii) {
            if (IsadoreData.bins[ii] == bin) {
                if (ii < IsadoreData.bins.length - 1) {
                    return IsadoreData.bins[ii + 1];
                } else {
                    return IsadoreData.bins[0];
                }
            }
        }
    };
    /**
     * Gets previous bin by position.
     *
     * @param bin
     *            The current bin where you want the bin to the right of this
     *            one.
     */
    var getPreviousBin = function (bin) {
        var ii;
        for (ii = 0; ii < IsadoreData.bins.length; ++ii) {
            if (IsadoreData.bins[ii] == bin) {
                if (ii > 0) {
                    return IsadoreData.bins[ii - 1];
                } else {
                    return IsadoreData.bins[IsadoreData.bins.length - 1];
                }
            }
        }
    };

	
	var updateTab = function(event, ui) {
		if(currentBin) {
			tabIndex = tabs.tabs('option', 'selected'); 
			console.info('Update tab'+tabIndex);
			self.tabHandlers[tabIndex].refresh(currentBin);
		}
	};
	
	/**
	 * Event handler to open bin on a click event of a object with data-bin_id
	 * attribute.
	 */
	this.binClick = function(event) {
		/* Click event handler for current settings bin lightbox */
		var binId = event.currentTarget.getAttribute('data-bin_id');
		self.open(binId);
	};
	
	/** Open bin lightbox. */
	this.open = function(binId, bin) {
		if(!bin) {
			bin = IsadoreData.getBin(binId);
			if(!bin) {
				console.error('No bin to open.');
				return;
				//TODO: Update with error message?
			}
		}
		currentBin = bin;
		dialog.setTitle(bin.name);
		console.log(binId);
		$('#bin_lightbox_fadewrapper').show();
		if(dialog.isOpen()) {
			updateTab();
		} else {
			dialog.open();
		}
		/*
		 * $('#bin_lightbox_devices_table').dataTable( { "sScrollY": "260px",
		 * "bDestroy": true, "bPaginate": false, "bFilter": false,
		 * "aoColumnDefs": [ {"bSortable": false, "aTargets": [3] } ] } );
		 */
	};
	init();
}
