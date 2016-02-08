import React from 'react';
import Question from 'components/question';
import AppStore from 'store/appStore';

export default React.createClass({
  displayName: 'Topics',

  propTypes: {
    topics: React.PropTypes.array.isRequired
  },

  contextTypes: {
    params: React.PropTypes.object.isRequired
  },

  childContextTypes: {
    topics: React.PropTypes.array.isRequired,
    params: React.PropTypes.object.isRequired
  },

  getChildContext() {
    return {
      topics: this.props.topics,
      params: this.context.params
    };
  },

  getInitialState() {
    return AppStore.getState();
  },

  render() {
    return (
      <div>
        <Question/>
      </div>
    );
  }

});
