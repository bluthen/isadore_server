from isadoreapp import app
from flask import abort, jsonify
from isadoreapp.authentication import authorized
import isadoreapp.util as util


@app.route('/resources/privileges', methods=["GET"])
@authorized('User')
def privileges_list():
    ids = util.getIdsFromTable("privilege")
    return jsonify({'xlink': ['/resources/privileges/' + str(privilege_id) for privilege_id in ids]})


@app.route('/resources/privileges/<int:privilege_id>', methods=["GET"])
@authorized('User')
def privileges_get(privilege_id):
    row = util.getRowFromTableById('privilege', int(privilege_id))
    # print row
    if row:
        return jsonify(row)
    else:
        abort(404, "Privilege not found.")


@app.route('/resources/privileges-fast', methods=["GET"])
@authorized('User')
def fast_privileges_list():
    rows = util.getRowsFromTable("privilege")
    return jsonify({'privileges': rows})
