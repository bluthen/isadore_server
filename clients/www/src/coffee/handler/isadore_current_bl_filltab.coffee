#   Copyright 2010-2019 Dan Elliott, Russell Valentine
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

class window.FillTab
    constructor: () ->
        self = this
        self.currentBin_ = null
        self.fill_ = null
        $('#bin_lightbox_fill_edit').click(() -> self.editClick_())
        $('#bin_lightbox_fill_new').click(() -> self.newClick_())

    reopenBinLightbox_: () ->
        self = this
        self.refresh(self.currentBin_)

    _getYear: (yfill) ->
        if yfill.filled_datetime?
            year = newDate(yfill.filled_datetime).getFullYear()
        else
            year = newDate(yfill.air_begin_datetime).getFullYear()
        return year;


    editClick_: () ->
        self = this
        lightboxHandlers.editFillLightbox.open({
            year: self._getYear(self.fill),
            fill_id: self.fill.id,
            customCloseCallback: () -> self.reopenBinLightbox_()
        })

    newClick_: () ->
        self = this
        lightboxHandlers.editFillLightbox.open({
            year: new Date().getFullYear()
            bin_id: self.currentBin_.id
            customCloseCallback: () ->
                self.reopenBinLightbox_()
        })

    refreshNonArrayForm_: () ->
        self = this
        $('#bin_lightbox_fillinfo_fillnumber').html(self.fill.fill_number)
        $('#bin_lightbox_fillinfo_fill_type').text(_.find(IsadoreData.fillTypes, {id: self.fill.fill_type_id}).name)
        $('#bin_lightbox_fillinfo_bin').html(self.fill.bin_id)

        if not IsadoreData.general.multiple_rolls
            $('#bin_lightbox_fillinfo_single_roll_option').show()
            $('#bin_lightbox_fill_info_multiple_rolls_option').hide()
        else
            $('#bin_lightbox_fillinfo_single_roll_option').hide()
            $('#bin_lightbox_fill_info_multiple_rolls_option').show()
        # Blank all the non-required fields
        $('#bin_lightbox_fillinfo_start, #bin_lightbox_fillinfo_end, #bin_lightbox_fillinfo_filled, #bin_lightbox_fillinfo_emptied, #bin_lightbox_fillinfo_rotationnumber, #bin_lightbox_fillinfo_hybridcode, #bin_lightbox_fillinfo_fieldcode, #bin_lightbox_fillinfo_truck, #bin_lightbox_fillinfo_lotnumber, #bin_lightbox_fillinfo_storagebinnumber, #bin_lightbox_fillinfo_storagebincode, #bin_lightbox_fillinfo_bushels, #bin_lightbox_fillinfo_single_roll').each(
            (index, value) ->
                $(value).html('')
        )

        if self.fill.filled_datetime
            $('#bin_lightbox_fillinfo_filled').html(
                HTMLHelper.dateToReadableO2(newDate(self.fill.filled_datetime)))

        if self.fill.emptied_datetime
            $('#bin_lightbox_fillinfo_emptied').html(
                HTMLHelper.dateToReadableO2(newDate(self.fill.emptied_datetime)))
        if self.fill.air_begin_datetime
            $('#bin_lightbox_fillinfo_start').html(
                HTMLHelper.dateToReadableO2(newDate(self.fill.air_begin_datetime)))

        if self.fill.air_end_datetime
            $('#bin_lightbox_fillinfo_end').html(
                HTMLHelper.dateToReadableO2(newDate(self.fill.air_end_datetime)))


        if self.fill.roll_datetime && self.fill.roll_datetime.length > 0
            $('#bin_lightbox_fillinfo_single_roll').html(
                HTMLHelper
                .dateToReadableO2(newDate(self.fill.roll_datetime[0])))

        if self.fill.rotation_number
            $('#bin_lightbox_fillinfo_rotationnumber').html(self.fill.rotation_number)

        if self.fill.hybrid_code
            $('#bin_lightbox_fillinfo_hybridcode').html(self.fill.hybrid_code.replace("\n", '</br>'))

        if self.fill.field_code
            $('#bin_lightbox_fillinfo_fieldcode').html(self.fill.field_code.replace("\n", '</br>'))

        if self.fill.truck
            $('#bin_lightbox_fillinfo_truck').html(self.fill.truck.replace("\n", '</br>'))

        if self.fill.lot_number
            $('#bin_lightbox_fillinfo_lotnumber').html(self.fill.lot_number)

        if self.fill.storage_bin_number
            $('#bin_lightbox_fillinfo_storagebinnumber').html(self.fill.storage_bin_number)

        if self.fill.storage_bin_code
            $('#bin_lightbox_fillinfo_storagebincode').html(self.fill.storage_bin_code)
        if self.fill.bushels
            $('#bin_lightbox_fillinfo_bushels').html(self.fill.bushels)


# Updates the page with current fill roll information.
    refreshRolls_: () ->
        self = this
        html = []
        if self.fill.roll_datetime
            for rdt in self.fill.roll_datetime
                html.push('<li><span class="roll_date">');
                html.push(HTMLHelper.dateToReadableO2(newDate(rdt)))
                html.push('</span>');
                html.push('</li>');
        ul = $('#bin_lightbox_fillinfo_rolls ul')
        ul.html(html.join(''))

# Updates the page with current fill mc data.
    refreshMC_: () ->
        self = this
        labels = ["pre_mc", "post_mc"]
        if IsadoreData.general.during_mc
            labels.push("during_mc")
        for label in labels
            html = []
            arr = self.fill[label]
            if arr
                for mc in arr
                    html.push('<li><span class="mc_value">')
                    if label == "during_mc"
                        html.push(mc[0].toFixed(1))
                        html.push('%')
                        html.push(" ")
                        html.push(HTMLHelper.dateToReadableO2(newDate(mc[1])));
                    else
                        html.push(mc.toFixed(1))
                        html.push('%')
                    html.push('</span>')
                    html.push('</li>')
            ul = $('#bin_lightbox_fillinfo_' + label)
            ul.html(html.join(''))


    _refresh2: (foundFill) ->
        self = this
        if self.currentBin_.name.split(' ')[0] != 'Bin'
            $('#bin_lightbox_fill_info_na_binname').html(self.currentBin_.name)
            $('#bin_lightbox_fillinfo_na').show()
            $('#bin_lightbox_fill_buttons').hide()
            $('#bin_lightbox_fillinfo_nonexist').hide()
            $('#bin_lightbox_fillinfo_exist').hide()

            $('#bin_lightbox_fill_spinner').hide()
            $('#bin_lightbox_fill_wrapper').show()
            return
        $('#bin_lightbox_fill_buttons').show()
        $('#bin_lightbox_fillinfo_na').hide()

        self.fill = foundFill
        if not self.fill
            $('#bin_lightbox_fillinfo_nonexist').show()
            $('#bin_lightbox_fillinfo_exist').hide()
            $('#bin_lightbox_fill_edit').hide()
        else
            self.refreshNonArrayForm_()
            self.refreshRolls_()
            self.refreshMC_()
            $('#bin_lightbox_fillinfo_nonexist').hide()
            $('#bin_lightbox_fillinfo_exist').show()
            $('#bin_lightbox_fill_edit').show()
        $('#bin_lightbox_fill_spinner').hide()
        $('#bin_lightbox_fill_wrapper').show()
        cbResize()

    refresh: (bin) ->
        self = this
        $('#bin_lightbox_fill_wrapper').hide()
        $('#bin_lightbox_fill_spinner').show()
        self.currentBin_ = bin
        self.fill = null
        DataManager.getFills({
            year: new Date().getFullYear(),
            callback: (d) =>
                fills = d.fills;
                fill = CurrentDataUtil.getBinFill(fills, bin.id, false)
                if _.isEmpty(fill)
                    fill = null
                self._refresh2(fill)
        })

