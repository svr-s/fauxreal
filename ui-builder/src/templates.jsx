import React from 'react';
import { Plus, X, ChevronDown, ChevronRight } from 'lucide-react';

export const CustomFieldTemplate = (props) => {
  const { id, classNames, label, help, required, description, errors, children, schema } = props;
  
  // RJSF passes a lot of things. If it's an object/array, we just render children directly 
  // because the Object/Array templates will handle their own layout.
  if (schema.type === 'object' || schema.type === 'array') {
    return (
      <div className={classNames}>
        {children}
        {errors}
        {help}
      </div>
    );
  }

  return (
    <div className={`form-group flex flex-col sm:flex-row sm:items-center mb-4 group ${classNames}`}>
      <div className="sm:w-1/3 pr-4 mb-1 sm:mb-0">
        <label htmlFor={id} className="block text-sm font-medium text-[var(--color-text-main)] group-focus-within:text-[var(--color-primary)] transition-colors">
          {label}
          {required && <span className="text-red-500 ml-1" title="Required">*</span>}
        </label>
        {description && <div className="text-xs text-[var(--color-text-muted)] mt-1">{description}</div>}
      </div>
      <div className="sm:w-2/3 relative flex-1">
        {children}
        {!required && (
          <span className="absolute right-3 top-2.5 text-xs text-gray-500 pointer-events-none opacity-50">
            optional
          </span>
        )}
        {errors}
        {help}
      </div>
    </div>
  );
};

export const CustomObjectFieldTemplate = (props) => {
  const { title, properties, required, description, uiSchema, idSchema } = props;
  
  // Root doesn't need indentation
  const isRoot = idSchema.$id === "root";
  
  return (
    <div className={`${!isRoot ? 'ml-4 pl-4 border-l-2 border-[var(--color-border)] focus-within:border-[var(--color-primary)] transition-colors' : ''}`}>
      {title && !isRoot && (
        <h3 className="text-md font-semibold text-[var(--color-text-main)] mb-3">
          {title}
        </h3>
      )}
      {description && <p className="text-xs text-[var(--color-text-muted)] mb-3">{description}</p>}
      <div className="space-y-2">
        {properties.map(element => (
          <div key={element.content.key} className="object-property">
            {element.content}
          </div>
        ))}
      </div>
    </div>
  );
};

export const CustomArrayFieldTemplate = (props) => {
  const { title, items, canAdd, onAddClick, required, schema } = props;
  
  return (
    <div className="mb-6">
      {title && (
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-md font-semibold text-[var(--color-text-main)]">
            {title}
            {required && <span className="text-red-500 ml-1">*</span>}
          </h3>
        </div>
      )}
      
      <div className="space-y-3">
        {items.map(element => (
          <div key={element.key} className="relative bg-[rgba(255,255,255,0.02)] border border-[var(--color-border)] focus-within:border-[var(--color-primary)] focus-within:bg-[rgba(167,139,250,0.02)] rounded-lg p-4 pt-6 transition-all group/item">
            {element.hasRemove && (
              <button 
                type="button" 
                onClick={element.onDropIndexClick(element.index)}
                className="absolute top-2 right-2 text-gray-500 hover:text-red-400 hover:bg-red-400/10 p-1 rounded transition-colors"
                title="Remove"
              >
                <X size={16} />
              </button>
            )}
            {element.children}
          </div>
        ))}
      </div>
      
      {canAdd && (
        <button 
          type="button"
          onClick={onAddClick}
          className="mt-3 flex items-center justify-center gap-2 w-full py-2 px-4 rounded-md border border-dashed border-[var(--color-border)] text-[var(--color-text-muted)] hover:text-[var(--color-primary)] hover:border-[var(--color-primary)] hover:bg-[rgba(167,139,250,0.05)] transition-all"
        >
          <Plus size={16} />
          Add {title || 'Item'}
        </button>
      )}
    </div>
  );
};
