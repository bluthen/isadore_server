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

class window.DataManager
    @_CHECK_EVENT_INTERVAL: 10000

    @_reset: () ->
        @_data = {}
        @_subscriptionId = null
        @_serverSubs = {'subscriptions': []}
        @_jsSubs = {}
        @_subInterval = null
        @_getFillLock = false
        @_getFillQueue = []

    @_startInterval: () ->
        if not @_subInterval?
            @_subInterval = setInterval(
                () =>
                    @_checkEvents()
            @_CHECK_EVENT_INTERVAL)

    @_checkEvents: () ->
        ###
      Checks with the server to see if there are new events.
    ###
        if @_subscriptionId?
            #Ajax call to get subscription events
            $.ajax({
                url: "../resources/subscription_event/#{@_subscriptionId}"
                type: 'DELETE'
                dataType: 'json'
                success: (data) =>
                    #for each event
                    for e in data.events
                        @_processEvent(JSON.parse(e.event))
                error: (jqXHR) =>
                    #Reset
                    if jqXHR.statusCode == 404
                        @_reset()
            })

    @_serverSubscribe: (sub, cb) ->
        if not @_subscriptionId
            $.ajax({
                url: '../resources/subscription'
                type: 'POST'
                dataType: 'json'
                success: (data) =>
                    @_subscriptionId = data.subscriber_id
                    @_serverSubscribe2(sub, cb)
                error: (jqXHR, textStatus, errorThrown) =>
                    console?.error?("#{textStatus} - #{errorThrown}")
                    cb?()
            })
        else
            @_serverSubscribe2(sub, cb)

    @_serverSubscribe2: (sub, cb) ->
        @_serverSubs.subscriptions.push(sub)
        $.ajax({
            url: "../resources/subscription/#{@_subscriptionId}"
            type: 'PUT'
            dataType: 'text'
            data: {subscribed: JSON.stringify(@_serverSubs)}
            success: () ->
                cb?()
            error: (jqXHR, textStatus, errorThrown) =>
                console?.trace?()
                console?.error?("#{textStatus} - #{errorThrown}")
                cb?()
        })

    @_getFill: (year, cb) ->
        # If we don't have this years fill year
        if @_getFillLock
            @_getFillQueue.push(() =>
                @_getFill(year, cb)
            )
            return
        if not @_data.fill?[year]
            # Subscribe to changes for this year's fill
            @_getFillLock = true
            fetchFills = () =>
                # Fetch entire years fill using fill-fast
                startYear = new Date(year, 0, 1, 0, 0, 0, 0)
                endYear = new Date(year, 11, 31, 23, 59, 59, 999);
                $.ajax({
                    url: '../resources/data/fills-fast'
                    type: 'GET'
                    dataType: 'json'
                    data: {
                        'begin_span1' : HTMLHelper.dateToParamString(startYear),
                        'begin_span2' : HTMLHelper.dateToParamString(endYear)
                    }
                    success: (data) =>
                        if not @_data.fill?
                            @_data.fill = {}
                        @_data.fill[year] = data.fills
                        try
                            cb?(@_data.fill[year])
                        finally
                            @_getFillLock = false
                            while @_getFillQueue.length > 0
                                f = @_getFillQueue.splice(0, 1)[0]
                                f?()
                    error: (jqXHR, textStatus, errorThrown) =>
                        console?.error?("#{textStatus} - #{errorThrown}")
                        @_getFillLock = false
                        while @_getFillQueue.length > 0
                            f = @_getFillQueue.splice(0, 1)[0]
                            f?()
                })
            @_serverSubscribe({key: 'fill', type: ['edit', 'add', 'delete'], year: year, self_events: false},
                fetchFills
            )
        else
            cb?(@_data.fill[year])

    @_removeExistingFills: (year, fill_ids) ->
        ###
        @param year The year to look for ids to remove.
        @params fill_ids ids to remove if exist.
        ###
        _.remove(@_data.fill[year], (f) ->
            return f.id in fill_ids
        )

    @_processEvent: (event) ->
        ###
      Process event from a publish or REST found event
      @params event.key
      @params event.type {string} one of 'edit', 'delete', 'add'
      @params event.ids {array of numbers}
      @params event.year {number} (required if type='fill')
      @params event.when {ISO8601 datestring} (optional)
      @params event.data (optional) Updated object to hold in manager, for fill key event it should be {fills: [{fill}, ...]}.
        ###
        # if event.key == 'fill' and if we have fill year's data
        if event.key? and event.key == 'fill' and @_data.fill?[event.year]
            if event.type in ['delete', 'edit']
                @_removeExistingFills(event.year, event.ids)
            if event.type in ['add', 'edit']
                if event.data?.fills?
                    # If event.data copy event.data add that to our data
                    for fill in event.data.fills
                        @_data.fill[event.year].push(_.cloneDeep(fill))
                        @_processEventCallbacks(event)
                else
                    finished = {}
                    for fillId in event.ids
                        finished[fillId] = false
                    for fillId in event.ids
                        $.ajax({
                            url: "../resources/data/fills/#{fillId}"
                            type: 'GET'
                            dataType: 'json'
                            success: (data) =>
                                @_removeExistingFills(event.year, [data.id])
                                @_data.fill[event.year].push(data)
                                finished[data.id] = data
                                if _.every(finished)
                                    event.data = {fills: _.toArray(finished)}
                                    @_processEventCallbacks(event)
                        })
            else
                @_processEventCallbacks(event)
        else
            console?.warn?('_processEvent, unsupported event.key')

    @_processEventCallbacks: (event) ->
        ###
      Goes through js subscriptions and calls the callback of any subscriptions matching event.
      @param event the event to do callbacks for.
    ###
    #Currently only fill key is supported
        for sid, sub of @_jsSubs
            #Go through subscriptions
            if (
                    sub.key == 'fill' and event.key == sub.key and event.year == sub.year and
                    (event.type == sub.type or (_.isArray(sub.type) and event.type in sub.type))
            )
                #If subscription matches event
                if sub.ids? and _.intersection(event.ids, sub.ids).length() > 0
                    #Call subscriptions callback with copy of event
                    e = _.cloneDeep(event)
                    e.data.fills = _.filter(e.data.fills, (f) -> f.id in sub.ids)
                    sub.callback?(e)
                else
                    sub.callback?(_.cloneDeep(event))

    @getFills: (args) ->
        ###
      Get request fills ids from year, if no ids will give entire year. This will fetch it from server if not cached,
      otherwise returns cached data. This attempts to keep cache updated.
      @param args.year {number} The year of fills to get
      @param args.ids {array of numbers} (optional) ids you want from that year.
      @param args.callback {function} function(data) The callback to call with own copy of the data.
        Example data
          {'fills': [{filldata}, {filldata}, ...}]}
        ###
        # Get data requested
        args.year = parseInt(args.year, 10)
        if args.ids?
            for i in [0...args.ids.length]
                args.ids[i] = parseInt(args.ids[i], 10)
        @_getFill(
            args.year,
            (fills) =>
                f = {'fills': []}
                if args.ids?
                    #Take out fills with id that we want
                    for fill in fills
                        if fill.id in args.ids
                            f.fills.push(fill)
                    # Callback with copy of data
                    args.callback?(_.cloneDeep(f))
                else
                    # Callback with copy of data
                    args.callback?({fills: _.cloneDeep(fills)})
        )
    @dataSub: (args) ->
        ###
      Subscribe to data change events.
      @param args.key {string} Only value for this currently support is 'fill'
      @param args.type {array of strings} valid strings are 'edit', 'add', 'delete'
      @params args.ids {array of numbers} (optional) valid with 'edit'/'delete' type, which key ids should trigger the event.
      @params args.year {number} (required for key='fill') Which year we are listening for.
      @param args.callback {function} function(data) data is of format {key: args.key, type: type, ids: [id1, .., idn], year: year, data: newdata}
      @returns subscription id to use with @dataUnSub
        ###
        if args.key == 'fill'
            @_getFill(args.year)
            # add subscription to subscribers list
            id = _.uniqueId('dataSub_')
            @_jsSubs[id] = args
        else
            throw "Unsuported key type."
        #Return subscription id
        return id

    @dataUnSub: (id) ->
        ###
      Unsubscribes from data event.
      @param id The id returned by @dataSub
    ###
        delete @_jsSubs[id]

    @dataPub: (event) ->
        ###
      Publish a data change event.
      @param event.key {string} Only value for this currently support is 'fill'
      @param event.type {string} Valid values are 'edit', 'add', 'delete'
      @param event.year {number} (required for key='fill') Which year event is for
      @param event.data {object} replacement object if type = 'edit', 'add', null if type='delete'
        ###
        @_processEvent(_.cloneDeep(event))

    @getRestSubscriberId: () ->
        ###
      Get the subscription id assigned to this client.
      @return uuid of subscription id that is used in rest api.
        ###
        return @_subscriptionId;


$(document).ready( () ->
    DataManager._reset()
    DataManager._startInterval()
)
