const initialState = Object.assign({
  currTask: null,
  queue: [-1],
  review: false,
  curr_question_id: -1,
  answer_selected: {},
  highlighter_color: {},
  saveAndNext: null
}, {});

export function quiz(state = initialState, action) {
  console.log(action);
  console.log(state.queue);
  switch(action.type) {
    case 'CLEAR_ANSWERS':
      return {
        ...state,
        answer_selected: {},
        curr_question_id: -1,
        highlighter_color: {},
        queue: []
      }
    case 'FETCH_QUESTION':
      return {
        ...state,
        question: {
          isFetching: true
        }
      }
    case 'FETCH_TASK_SUCCESS':
      return {
        ...state,
        currTask: action.task
      }
    case 'ANSWER_SELECTED':
      var temp = Object.assign({}, state.answer_selected);
      var new_ans = {
        answer_id: action.answer_id,
        question_id: action.question_id,
        question_type: action.question_type,
        text: action.text,
      };
      if(temp[action.question_id] && action.question_type == 'CHECKBOX') {
          temp[action.question_id].push(new_ans);
      } else{
        temp[action.question_id] = [new_ans];
      }
      return {
          ...state,
          answer_selected: temp
      }
    case 'ANSWER_REMOVED':
      var ans_array = state.answer_selected[action.question_id];
      var ind = -1;
      for(var i = 0; i < ans_array.length; i++) {
        if(ans_array[i].answer_id == action.answer_id) {
          ind = i;
          break;
        }
      }
      if(i > -1) {
        var temp = Object.assign({}, state.answer_selected);
        temp[action.question_id].splice(ind, 1);
        return {
          ...state,
          answer_selected: temp
        };
      }
      return state;
    case 'UPDATE_REVIEW':
      return {
        ...state,
        review: action.review
      }
    case 'COLOR_SELECTED':
      var assign_dict = { question_id: action.question_id, answer_id: action.answer_id, color: action.color };
      return {
        ...state,
        highlighter_color: assign_dict
      }
    case 'UPDATE_QUEUE':
      var new_queue = Object.assign([], state.queue);
      var ind = new_queue.indexOf(state.curr_question_id);
      for(var i = 0; i < action.questions.length; i++) {
        if(state.queue.indexOf(action.questions[i]) == -1) {
          new_queue.splice(ind + i + 1, 0, action.questions[i]);
        }
      }
      return {
        ...state,
        queue: new_queue
      }
    case 'REMOVE_QUEUE':
      var new_queue = Object.assign([], state.queue);
      for(var i = 0; i < action.questions.length; i++) {
        var ind = new_queue.indexOf(action.questions[i].id);
        if(ind != -1) {
          new_queue.splice(ind, 1);
        }
      }
      return {
        ...state,
        queue: new_queue
      }
    case 'UPDATE_ACTIVE_QUESTION':
      return {
        ...state,
        curr_question_id: action.q_id
      }
    case 'POST_QUIZ_CALLBACK':
      return {
        ...state,
        saveAndNext: action.saveAndNext
      }
    default:
      return state;
  }
}
