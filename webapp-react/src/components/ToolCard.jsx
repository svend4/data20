import { getCategoryDisplayName, getToolIcon } from '../utils/api';
import './ToolCard.css';

const ToolCard = ({ tool, onClick }) => {
  const paramsCount = tool.parameters ? Object.keys(tool.parameters).length : 0;
  const requiredParams = tool.parameters
    ? Object.values(tool.parameters).filter((p) => p.required).length
    : 0;

  return (
    <div className="tool-card card" onClick={onClick}>
      <div className="tool-category">
        {getCategoryDisplayName(tool.category || 'other')}
      </div>
      <h3>
        <span className="tool-icon">{getToolIcon(tool.category)}</span>
        {tool.display_name || tool.name}
      </h3>
      <p>{tool.description || 'Описание недоступно'}</p>
      <div className="tool-params">
        📝 Параметров: {paramsCount}{' '}
        {requiredParams > 0 ? `(${requiredParams} обязательных)` : ''}
      </div>
    </div>
  );
};

export default ToolCard;
