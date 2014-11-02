from flask import Blueprint, render_template, redirect, url_for, current_app,\
                  request

expert = Blueprint('expert', __name__)

@expert.route('/expert/form')
def expert_form():
  return "yea"
